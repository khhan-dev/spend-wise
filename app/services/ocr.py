"""영수증 OCR 서비스.

- StubOcrProvider: 미연동 상태. 항상 실패를 반환해 프론트가 수동 입력으로 폴백한다.
- ClovaOcrProvider: Naver CLOVA OCR(Receipt Specialization) 연동. Invoke URL + Secret 설정 시 활성화.

CLOVA 자격증명은 환경변수(CLOVA_OCR_INVOKE_URL, CLOVA_OCR_SECRET)로만 주입하며
소스/깃에 하드코딩하지 않는다.
"""

import base64
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from functools import lru_cache

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 15.0


@dataclass
class OcrResult:
    success: bool
    fields: dict = field(default_factory=dict)  # tx_date, vendor_name, vendor_biz_no, total_amount
    confidence: float = 0.0
    raw: dict = field(default_factory=dict)


class OcrProvider:
    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:  # pragma: no cover
        raise NotImplementedError


class StubOcrProvider(OcrProvider):
    """미연동 스텁 — 항상 실패를 반환해 수동 입력을 유도한다."""

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        return OcrResult(success=False, fields={}, confidence=0.0, raw={"note": "OCR 미연동(스텁)"})


# ── CLOVA 응답 파싱 헬퍼 ─────────────────────────
def _node_text(node: object) -> str | None:
    """CLOVA 필드 노드({"text": ...})에서 텍스트 추출."""
    if isinstance(node, dict):
        txt = node.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt.strip()
    return None


def _parse_amount(node: object) -> int | None:
    """가격 노드에서 정수(원) 추출. formatted.value 우선, 없으면 숫자만 추출."""
    if not isinstance(node, dict):
        return None
    fmt = node.get("formatted")
    if isinstance(fmt, dict) and str(fmt.get("value", "")).strip():
        digits = re.sub(r"[^\d]", "", str(fmt["value"]))
        if digits:
            return int(digits)
    txt = _node_text(node)
    if txt:
        digits = re.sub(r"[^\d]", "", txt)
        if digits:
            return int(digits)
    return None


def _parse_date(node: object) -> str | None:
    """날짜 노드에서 YYYY-MM-DD 정규화. 실패 시 원문 반환(사용자가 보정)."""
    if not isinstance(node, dict):
        return None
    fmt = node.get("formatted")
    if isinstance(fmt, dict):
        y, m, d = fmt.get("year"), fmt.get("month"), fmt.get("day")
        if y and m and d:
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    txt = _node_text(node)
    if txt:
        match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", txt)
        if match:
            y, m, d = match.groups()
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        return txt
    return None


def parse_clova_receipt(data: dict) -> OcrResult:
    """CLOVA Receipt OCR 응답 → 표준 OcrResult."""
    images = data.get("images") or []
    if not images:
        return OcrResult(success=False, raw={"note": "empty images"})

    img = images[0]
    if img.get("inferResult") not in (None, "SUCCESS"):
        return OcrResult(success=False, raw={"inferResult": img.get("inferResult")})

    result = (img.get("receipt") or {}).get("result") or {}
    store = result.get("storeInfo") or {}
    payment = result.get("paymentInfo") or {}
    total = result.get("totalPrice") or {}

    fields: dict = {}
    vendor = _node_text(store.get("name"))
    biz_no = _node_text(store.get("bizNum"))
    tx_date = _parse_date(payment.get("date"))
    total_amount = _parse_amount(total.get("price"))

    if vendor:
        fields["vendor_name"] = vendor
    if biz_no:
        fields["vendor_biz_no"] = biz_no
    if tx_date:
        fields["tx_date"] = tx_date
    if total_amount is not None:
        fields["total_amount"] = total_amount

    # 합계금액을 뽑았으면 신뢰, 일부만 뽑았으면 낮은 신뢰, 아무것도 없으면 실패
    if total_amount is not None:
        return OcrResult(success=True, fields=fields, confidence=0.9)
    if fields:
        return OcrResult(success=True, fields=fields, confidence=0.4)
    return OcrResult(success=False, fields={}, confidence=0.0)


class ClovaOcrProvider(OcrProvider):
    """Naver CLOVA OCR(Receipt) 연동."""

    def __init__(self, invoke_url: str, secret: str):
        self.invoke_url = invoke_url
        self.secret = secret

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        fmt = "png" if content_type and "png" in content_type.lower() else "jpg"
        payload = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "images": [
                {
                    "format": fmt,
                    "name": "receipt",
                    "data": base64.b64encode(image_bytes).decode(),
                }
            ],
        }
        headers = {"X-OCR-SECRET": self.secret, "Content-Type": "application/json"}
        try:
            resp = httpx.post(self.invoke_url, json=payload, headers=headers, timeout=_HTTP_TIMEOUT)
            resp.raise_for_status()
            return parse_clova_receipt(resp.json())
        except Exception as exc:  # 네트워크·인증·파싱 실패 → 수동 입력 폴백
            logger.warning("CLOVA OCR 호출 실패: %s", exc)  # 시크릿은 로깅하지 않음
            return OcrResult(success=False, fields={}, confidence=0.0, raw={"error": type(exc).__name__})


@lru_cache
def get_ocr_provider() -> OcrProvider:
    """설정에 CLOVA 자격증명이 있으면 실연동, 없으면 스텁."""
    if settings.clova_ocr_enabled:
        return ClovaOcrProvider(settings.clova_ocr_invoke_url, settings.clova_ocr_secret)
    return StubOcrProvider()
