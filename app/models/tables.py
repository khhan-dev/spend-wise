import datetime as dt
import uuid

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    ApprovalAction,
    EvidenceType,
    OcrStatus,
    PayMethod,
    ReportStatus,
    Role,
)


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def _created() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


# ── 조직 ─────────────────────────────────────────
class Company(Base):
    __tablename__ = "company"

    id: Mapped[uuid.UUID] = _pk()
    biz_no: Mapped[str | None] = mapped_column(String(12))  # 사업자등록번호
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[dt.datetime] = _created()

    departments: Mapped[list["Department"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Department(Base):
    __tablename__ = "department"

    id: Mapped[uuid.UUID] = _pk()
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("company.id"))
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str | None] = mapped_column(String(30))

    company: Mapped["Company"] = relationship(back_populates="departments")
    teams: Mapped[list["Team"]] = relationship(
        back_populates="department", cascade="all, delete-orphan"
    )


class Team(Base):
    __tablename__ = "team"

    id: Mapped[uuid.UUID] = _pk()
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("department.id"))
    name: Mapped[str] = mapped_column(String(100))

    department: Mapped["Department"] = relationship(back_populates="teams")
    users: Mapped[list["User"]] = relationship(back_populates="team")


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = _pk()
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("team.id"))
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=20), default=Role.employee
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = _created()

    team: Mapped["Team"] = relationship(back_populates="users")


# ── 계정과목 / 거래처 마스터 ─────────────────────
class Account(Base):
    __tablename__ = "account"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(50), unique=True)  # 복리후생비 등
    default_deductible: Mapped[bool] = mapped_column(Boolean, default=True)  # 부가세 공제 기본값


class Vendor(Base):
    __tablename__ = "vendor"

    id: Mapped[uuid.UUID] = _pk()
    biz_no: Mapped[str | None] = mapped_column(String(12), index=True)
    name: Mapped[str] = mapped_column(String(200))


# ── 경비 ─────────────────────────────────────────
class ExpenseReport(Base):
    __tablename__ = "expense_report"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False, length=20), default=ReportStatus.draft
    )
    period: Mapped[str] = mapped_column(String(7))  # 귀속월 YYYY-MM
    created_at: Mapped[dt.datetime] = _created()
    submitted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship()
    items: Mapped[list["ExpenseItem"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    approvals: Mapped[list["ApprovalLog"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ExpenseItem(Base):
    __tablename__ = "expense_item"

    id: Mapped[uuid.UUID] = _pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expense_report.id"))
    account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendor.id"))
    closing_batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("closing_batch.id"))

    # 소속 스냅샷(등록 시점 배부, 이후 인사이동에도 귀속 유지)
    dept_snapshot: Mapped[str | None] = mapped_column(String(100))
    team_snapshot: Mapped[str | None] = mapped_column(String(100))

    tx_date: Mapped[dt.date] = mapped_column(Date)              # 사용일자
    supply_amount: Mapped[int] = mapped_column(BigInteger, default=0)  # 공급가액(원)
    vat_amount: Mapped[int] = mapped_column(BigInteger, default=0)     # 부가세액(원)
    total_amount: Mapped[int] = mapped_column(BigInteger, default=0)   # 합계금액(원)

    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, native_enum=False, length=20), default=EvidenceType.etc
    )
    vat_deductible: Mapped[bool] = mapped_column(Boolean, default=False)
    pay_method: Mapped[PayMethod] = mapped_column(
        Enum(PayMethod, native_enum=False, length=20), default=PayMethod.corporate_card
    )
    pjt_code: Mapped[str | None] = mapped_column(String(30))
    memo: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = _created()

    report: Mapped["ExpenseReport"] = relationship(back_populates="items")
    account: Mapped["Account"] = relationship()
    vendor: Mapped["Vendor"] = relationship()
    receipt: Mapped["Receipt"] = relationship(
        back_populates="item", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def vendor_name(self) -> str | None:
        return self.vendor.name if self.vendor else None

    @property
    def image_key(self) -> str | None:
        return self.receipt.image_key if self.receipt else None


class Receipt(Base):
    __tablename__ = "receipt"

    id: Mapped[uuid.UUID] = _pk()
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expense_item.id"), unique=True)
    image_key: Mapped[str | None] = mapped_column(String(500))  # 스토리지 키(로컬/S3)
    ocr_json: Mapped[dict | None] = mapped_column(JSON)          # OCR 추출 원본
    ocr_status: Mapped[OcrStatus] = mapped_column(
        Enum(OcrStatus, native_enum=False, length=20), default=OcrStatus.pending
    )

    item: Mapped["ExpenseItem"] = relationship(back_populates="receipt")


# ── 승인 이력 / 월 마감 ──────────────────────────
class ApprovalLog(Base):
    __tablename__ = "approval_log"

    id: Mapped[uuid.UUID] = _pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expense_report.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    action: Mapped[ApprovalAction] = mapped_column(Enum(ApprovalAction, native_enum=False, length=20))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = _created()

    report: Mapped["ExpenseReport"] = relationship(back_populates="approvals")
    actor: Mapped["User"] = relationship()


class ClosingBatch(Base):
    __tablename__ = "closing_batch"

    id: Mapped[uuid.UUID] = _pk()
    period: Mapped[str] = mapped_column(String(7), unique=True)  # YYYY-MM
    closed_at: Mapped[dt.datetime] = _created()
    export_key: Mapped[str | None] = mapped_column(String(500))  # 생성 엑셀 위치
