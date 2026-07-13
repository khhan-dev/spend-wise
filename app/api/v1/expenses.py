import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import (
    Account,
    ApprovalLog,
    ExpenseItem,
    ExpenseReport,
    Role,
    User,
    Vendor,
)
from app.models.enums import ApprovalAction, ReportStatus
from app.schemas.expense import (
    ExpenseItemIn,
    ExpenseReportCreate,
    ExpenseReportOut,
    ItemValidation,
)
from app.services import expense_rules

router = APIRouter(prefix="/expenses", tags=["expenses"])

# 작성자가 수정·삭제할 수 있는 상태
EDITABLE_STATES = (ReportStatus.draft, ReportStatus.rejected)


# ── 헬퍼 ─────────────────────────────────────────
def _user_org(user: User) -> tuple[str | None, str | None]:
    """신청자의 부서/팀명 스냅샷."""
    if user.team is None:
        return None, None
    dept = user.team.department.name if user.team.department else None
    return dept, user.team.name


def _build_item(db: Session, data: ExpenseItemIn, dept: str | None, team: str | None) -> ExpenseItem:
    # 금액 분리: 미입력 시 증빙유형 기준 자동
    if data.supply_amount is None or data.vat_amount is None:
        supply, vat = expense_rules.split_amount(data.total_amount, data.evidence_type)
    else:
        supply, vat = data.supply_amount, data.vat_amount

    # 부가세 공제여부: 미지정 시 계정 기본값 + 증빙 기준 자동
    account = db.get(Account, data.account_id) if data.account_id else None
    if data.vat_deductible is None:
        acct_default = account.default_deductible if account else False
        deductible = expense_rules.determine_deductible(data.evidence_type, acct_default)
    else:
        deductible = data.vat_deductible

    # 거래처 upsert(사업자번호 기준)
    vendor = None
    if data.vendor_biz_no:
        vendor = db.scalar(select(Vendor).where(Vendor.biz_no == data.vendor_biz_no))
    if vendor is None and (data.vendor_name or data.vendor_biz_no):
        vendor = Vendor(biz_no=data.vendor_biz_no, name=data.vendor_name or "")
        db.add(vendor)
        db.flush()

    return ExpenseItem(
        account_id=data.account_id,
        vendor_id=vendor.id if vendor else None,
        dept_snapshot=data.dept_snapshot or dept,
        team_snapshot=data.team_snapshot or team,
        tx_date=data.tx_date,
        supply_amount=supply,
        vat_amount=vat,
        total_amount=data.total_amount,
        evidence_type=data.evidence_type,
        vat_deductible=deductible,
        pay_method=data.pay_method,
        pjt_code=data.pjt_code,
        memo=data.memo,
    )


def _load_report_or_404(db: Session, report_id: uuid.UUID) -> ExpenseReport:
    report = db.get(ExpenseReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="신청서를 찾을 수 없습니다.")
    return report


def _can_view(user: User, report: ExpenseReport) -> bool:
    if user.role == Role.admin or report.user_id == user.id:
        return True
    if user.role == Role.manager and user.team_id and report.user.team_id == user.team_id:
        return True
    return False


# ── 엔드포인트 ───────────────────────────────────
@router.post("/reports", response_model=ExpenseReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    body: ExpenseReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """경비 신청서 작성 (소속 부서/팀 자동 배부)."""
    dept, team = _user_org(user)
    report = ExpenseReport(user_id=user.id, title=body.title, period=body.period, status=ReportStatus.draft)
    report.items = [_build_item(db, it, dept, team) for it in body.items]
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=list[ExpenseReportOut])
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """열람 범위: 직원=본인 / 팀장=소속 팀 / 관리자=전사."""
    stmt = select(ExpenseReport).order_by(ExpenseReport.created_at.desc())
    if user.role == Role.employee:
        stmt = stmt.where(ExpenseReport.user_id == user.id)
    elif user.role == Role.manager and user.team_id:
        stmt = stmt.join(User, ExpenseReport.user_id == User.id).where(User.team_id == user.team_id)
    return list(db.scalars(stmt))


@router.get("/reports/{report_id}", response_model=ExpenseReportOut)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = _load_report_or_404(db, report_id)
    if not _can_view(user, report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="열람 권한이 없습니다.")
    return report


def _require_owner_editable(report: ExpenseReport, user: User) -> None:
    if report.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 신청서만 수정할 수 있습니다.")
    if report.status not in EDITABLE_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="제출 이후에는 수정할 수 없습니다. 반려된 경우에만 다시 수정할 수 있습니다.",
        )


@router.put("/reports/{report_id}", response_model=ExpenseReportOut)
def update_report(
    report_id: uuid.UUID,
    body: ExpenseReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """신청서 전체 수정(제목·귀속월·항목 일괄 교체). 작성중/반려 상태의 본인 신청서만."""
    report = _load_report_or_404(db, report_id)
    _require_owner_editable(report, user)

    dept, team = _user_org(user)
    report.title = body.title
    report.period = body.period
    report.items = [_build_item(db, it, dept, team) for it in body.items]  # 기존 항목은 교체(삭제)
    db.commit()
    db.refresh(report)
    return report


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """신청서 삭제. 작성중/반려 상태의 본인 신청서만."""
    report = _load_report_or_404(db, report_id)
    _require_owner_editable(report, user)
    db.delete(report)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reports/{report_id}/submit", response_model=ExpenseReportOut)
def submit_report(report_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """작성중 → 제출 (본인만)."""
    report = _load_report_or_404(db, report_id)
    if report.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 신청서만 제출할 수 있습니다.")
    if report.status not in (ReportStatus.draft, ReportStatus.rejected):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="제출 가능한 상태가 아닙니다.")
    report.status = ReportStatus.submitted
    report.submitted_at = dt.datetime.now(dt.timezone.utc)
    db.add(ApprovalLog(report_id=report.id, actor_id=user.id, action=ApprovalAction.submit))
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}/validate", response_model=list[ItemValidation])
def validate_report(report_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """규칙 A(3만원 초과 비적격)·D(금액 일치) 검증 결과."""
    report = _load_report_or_404(db, report_id)
    if not _can_view(user, report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="열람 권한이 없습니다.")
    return [
        ItemValidation(
            item_id=it.id,
            evidence_warning=expense_rules.evidence_warning(it.total_amount, it.evidence_type),
            amount_ok=expense_rules.amount_ok(it.supply_amount, it.vat_amount, it.total_amount),
        )
        for it in report.items
    ]
