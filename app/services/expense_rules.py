"""경비 도메인 규칙 — 금액 분리, 부가세 공제 판정, 검증(§03 규칙 A·D)."""

from app.models.enums import EvidenceType

QUALIFIED_THRESHOLD = 30_000  # 3만원 초과 비적격 → 증빙불비가산세 대상

# 부가세가 포함되어 매입세액공제가 가능한 증빙(면세 계산서 제외)
_VAT_BEARING = {EvidenceType.tax_invoice, EvidenceType.card, EvidenceType.cash_receipt}


def split_amount(total: int, evidence_type: EvidenceType) -> tuple[int, int]:
    """합계금액을 공급가액/부가세로 분리. 면세·비적격은 전액 공급가액, 부가세 0."""
    if evidence_type in _VAT_BEARING:
        supply = round(total / 1.1)
        return supply, total - supply
    return total, 0


def determine_deductible(evidence_type: EvidenceType, account_default: bool) -> bool:
    """부가세 매입세액공제 여부. 적격+부가세 증빙이고 계정이 공제대상일 때만 True."""
    return evidence_type in _VAT_BEARING and account_default


def evidence_warning(total: int, evidence_type: EvidenceType) -> str | None:
    """규칙 A: 3만원 초과인데 비적격증빙이면 경고 문구."""
    if total > QUALIFIED_THRESHOLD and not evidence_type.is_qualified:
        return "⚠ 3만원 초과 비적격 증빙 — 증빙불비가산세(2%) 대상"
    return None


def amount_ok(supply: int, vat: int, total: int) -> bool:
    """규칙 D: 공급가액 + 부가세액 = 합계금액."""
    return supply + vat == total
