import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import ApprovalLog, ExpenseReport, Role, User
from app.models.enums import ApprovalAction, ReportStatus
from app.schemas.common import ApprovalIn, ApprovalRejectIn
from app.schemas.expense import ExpenseReportOut

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _get_report(db: Session, report_id: uuid.UUID) -> ExpenseReport:
    report = db.get(ExpenseReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="신청서를 찾을 수 없습니다.")
    return report


def _manager_owns_team(manager: User, report: ExpenseReport) -> bool:
    return bool(manager.team_id) and report.user.team_id == manager.team_id


@router.post("/{report_id}/approve", response_model=ExpenseReportOut)
def approve(
    report_id: uuid.UUID,
    body: ApprovalIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.manager, Role.admin)),
):
    """팀장 승인: 제출 → 팀장승인."""
    report = _get_report(db, report_id)
    if user.role == Role.manager and not _manager_owns_team(user, report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="소속 팀 신청서만 승인할 수 있습니다.")
    if report.status != ReportStatus.submitted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="제출 상태만 승인할 수 있습니다.")
    report.status = ReportStatus.team_approved
    db.add(ApprovalLog(report_id=report.id, actor_id=user.id, action=ApprovalAction.approve, comment=body.comment))
    db.commit()
    db.refresh(report)
    return report


@router.post("/{report_id}/reject", response_model=ExpenseReportOut)
def reject(
    report_id: uuid.UUID,
    body: ApprovalRejectIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.manager, Role.admin)),
):
    """반려(사유 필수): 어느 단계든 작성중으로 되돌림."""
    report = _get_report(db, report_id)
    if user.role == Role.manager and not _manager_owns_team(user, report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="소속 팀 신청서만 반려할 수 있습니다.")
    if report.status in (ReportStatus.closed,):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="마감된 신청서는 반려할 수 없습니다.")
    report.status = ReportStatus.rejected
    db.add(ApprovalLog(report_id=report.id, actor_id=user.id, action=ApprovalAction.reject, comment=body.comment))
    db.commit()
    db.refresh(report)
    return report


@router.post("/{report_id}/review", response_model=ExpenseReportOut)
def review(
    report_id: uuid.UUID,
    body: ApprovalIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
):
    """경영지원실 검토: 팀장승인 → 검토완료(마감 대상 편입)."""
    report = _get_report(db, report_id)
    if report.status != ReportStatus.team_approved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="팀장승인 상태만 검토할 수 있습니다.")
    report.status = ReportStatus.reviewed
    db.add(ApprovalLog(report_id=report.id, actor_id=user.id, action=ApprovalAction.review, comment=body.comment))
    db.commit()
    db.refresh(report)
    return report
