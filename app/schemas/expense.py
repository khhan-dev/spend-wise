import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EvidenceType, OcrStatus, PayMethod, ReportStatus


# ── 경비 항목 ────────────────────────────────────
class ExpenseItemIn(BaseModel):
    tx_date: dt.date
    total_amount: int = Field(ge=0)
    supply_amount: int | None = Field(default=None, ge=0)  # 미입력 시 서버가 자동 분리
    vat_amount: int | None = Field(default=None, ge=0)
    account_id: uuid.UUID | None = None
    vendor_name: str | None = None
    vendor_biz_no: str | None = None
    evidence_type: EvidenceType = EvidenceType.etc
    pay_method: PayMethod = PayMethod.corporate_card
    vat_deductible: bool | None = None  # 미지정 시 계정/증빙 기준 자동 판정
    pjt_code: str | None = None
    memo: str | None = None
    dept_snapshot: str | None = None  # 미지정 시 신청자 소속 자동 배부
    team_snapshot: str | None = None


class ExpenseItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tx_date: dt.date
    supply_amount: int
    vat_amount: int
    total_amount: int
    account_id: uuid.UUID | None
    vendor_name: str | None
    evidence_type: EvidenceType
    pay_method: PayMethod
    vat_deductible: bool
    dept_snapshot: str | None
    team_snapshot: str | None
    pjt_code: str | None
    memo: str | None


# ── 경비 신청서 ──────────────────────────────────
class ExpenseReportCreate(BaseModel):
    title: str
    period: str = Field(pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    items: list[ExpenseItemIn] = []


class ExpenseReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    period: str
    status: ReportStatus
    user_id: uuid.UUID
    created_at: dt.datetime
    items: list[ExpenseItemOut] = []


# ── 검증 결과(규칙 A·D) ─────────────────────────
class ItemValidation(BaseModel):
    item_id: uuid.UUID
    evidence_warning: str | None = None   # 규칙 A: 3만원 초과 비적격
    amount_ok: bool                        # 규칙 D: 공급+부가=합계
