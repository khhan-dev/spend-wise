"""영수증 OCR 서비스.

MVP에서는 실제 CLOVA OCR 연동 없이 인터페이스만 제공한다.
`extract()` 는 항상 실패(빈 초안)를 반환하므로 프론트는 자연스럽게
'수동 입력' 폴백으로 넘어간다. 실제 연동 시 ClovaOcrProvider 를 구현해
`extract()` 만 교체하면 된다.
"""

from dataclasses import dataclass, field


@dataclass
class OcrResult:
    success: bool
    fields: dict = field(default_factory=dict)  # tx_date, vendor_name, biz_no, total, vat ...
    confidence: float = 0.0
    raw: dict = field(default_factory=dict)


class OcrProvider:
    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:  # pragma: no cover
        raise NotImplementedError


class StubOcrProvider(OcrProvider):
    """미연동 스텁 — 항상 실패를 반환해 수동 입력을 유도한다."""

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        return OcrResult(success=False, fields={}, confidence=0.0, raw={"note": "OCR 미연동(스텁)"})


# TODO: Phase 1 후반 — Naver CLOVA OCR Provider 구현
# class ClovaOcrProvider(OcrProvider):
#     def __init__(self, invoke_url: str, secret: str): ...
#     def extract(self, image_bytes, content_type) -> OcrResult: ...


_provider: OcrProvider = StubOcrProvider()


def get_ocr_provider() -> OcrProvider:
    return _provider
