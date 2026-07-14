"""CLOVA OCR 파싱·연동 단위 테스트 (실제 API 호출 없이 목 사용)."""

import app.services.ocr as ocr_mod
from app.services.ocr import (
    ClovaOcrProvider,
    StubOcrProvider,
    parse_clova_receipt,
)

# CLOVA Receipt OCR 응답 샘플(축약)
SAMPLE_RESPONSE = {
    "version": "V2",
    "images": [
        {
            "inferResult": "SUCCESS",
            "receipt": {
                "result": {
                    "storeInfo": {
                        "name": {"text": "스타벅스 강남점"},
                        "bizNum": {"text": "123-45-67890"},
                    },
                    "paymentInfo": {
                        "date": {"text": "2026-07-02", "formatted": {"year": "2026", "month": "07", "day": "02"}}
                    },
                    "totalPrice": {"price": {"text": "5,000", "formatted": {"value": "5000"}}},
                }
            },
        }
    ],
}


def test_parse_receipt_extracts_fields():
    result = parse_clova_receipt(SAMPLE_RESPONSE)
    assert result.success is True
    assert result.confidence >= 0.9
    assert result.fields["vendor_name"] == "스타벅스 강남점"
    assert result.fields["vendor_biz_no"] == "123-45-67890"
    assert result.fields["tx_date"] == "2026-07-02"
    assert result.fields["total_amount"] == 5000


def test_parse_receipt_date_from_dotted_text():
    data = {
        "images": [
            {
                "inferResult": "SUCCESS",
                "receipt": {
                    "result": {
                        "paymentInfo": {"date": {"text": "2026.12.09 14:33"}},
                        "totalPrice": {"price": {"text": "12,300"}},
                    }
                },
            }
        ]
    }
    result = parse_clova_receipt(data)
    assert result.fields["tx_date"] == "2026-12-09"
    assert result.fields["total_amount"] == 12300


def test_parse_receipt_no_total_is_low_confidence():
    data = {"images": [{"inferResult": "SUCCESS", "receipt": {"result": {"storeInfo": {"name": {"text": "A"}}}}}]}
    result = parse_clova_receipt(data)
    assert result.success is True and result.confidence < 0.6


def test_parse_receipt_empty_fails():
    assert parse_clova_receipt({"images": []}).success is False
    assert parse_clova_receipt({"images": [{"inferResult": "ERROR"}]}).success is False


def test_stub_provider_returns_failure():
    """스텁은 항상 실패를 반환해 수동 입력 폴백을 유도한다(미연동 기본 경로)."""
    result = StubOcrProvider().extract(b"anybytes", "image/jpeg")
    assert result.success is False
    assert result.fields == {}
    assert result.confidence == 0.0


def test_clova_provider_success(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return SAMPLE_RESPONSE

    monkeypatch.setattr(ocr_mod.httpx, "post", lambda *a, **k: FakeResp())
    provider = ClovaOcrProvider("http://fake/infer", "secret")
    result = provider.extract(b"imgbytes", "image/jpeg")
    assert result.success and result.fields["total_amount"] == 5000


def test_clova_provider_network_error_falls_back(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(ocr_mod.httpx, "post", boom)
    provider = ClovaOcrProvider("http://fake/infer", "secret")
    result = provider.extract(b"imgbytes", "image/jpeg")
    assert result.success is False  # 실패 시 수동 입력 폴백


def test_provider_selection(monkeypatch):
    from app.core.config import settings

    # 미설정 → 스텁
    ocr_mod.get_ocr_provider.cache_clear()
    monkeypatch.setattr(settings, "clova_ocr_invoke_url", "", raising=False)
    monkeypatch.setattr(settings, "clova_ocr_secret", "", raising=False)
    assert isinstance(ocr_mod.get_ocr_provider(), StubOcrProvider)

    # 설정 → 실연동
    ocr_mod.get_ocr_provider.cache_clear()
    monkeypatch.setattr(settings, "clova_ocr_invoke_url", "http://fake/infer", raising=False)
    monkeypatch.setattr(settings, "clova_ocr_secret", "sekret", raising=False)
    assert isinstance(ocr_mod.get_ocr_provider(), ClovaOcrProvider)
    ocr_mod.get_ocr_provider.cache_clear()
