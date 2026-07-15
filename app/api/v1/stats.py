from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Account, ExpenseItem, ExpenseReport, Role, User
from app.models.enums import EvidenceType
from app.schemas.stats import DashboardStats, MonthAmount, NamedAmount

router = APIRouter(prefix="/stats", tags=["stats"])

_NON_QUALIFIED = [EvidenceType.simple_receipt, EvidenceType.etc]
_MISC = "미분류"


def _scoped_report_ids(db: Session, user: User) -> list:
    """열람 범위(직원=본인 / 팀장=소속 팀 / 관리자=전사)에 해당하는 신청서 id."""
    q = select(ExpenseReport.id)
    if user.role == Role.employee:
        q = q.where(ExpenseReport.user_id == user.id)
    elif user.role == Role.manager and user.team_id:
        q = q.join(User, ExpenseReport.user_id == User.id).where(User.team_id == user.team_id)
    return list(db.scalars(q))


def _sum(db: Session, *conditions) -> int:
    return int(db.scalar(select(func.coalesce(func.sum(ExpenseItem.total_amount), 0)).where(*conditions)) or 0)


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """대시보드 집계 — 합계·상태분포·계정/부서/월별 집계·공제·경고."""
    ids = _scoped_report_ids(db, user)
    empty = DashboardStats(
        total_amount=0, item_count=0, report_count=0, status_counts={},
        deductible_amount=0, non_deductible_amount=0, warning_count=0,
        by_account=[], by_dept=[], by_month=[],
    )
    if not ids:
        return empty

    scope = ExpenseItem.report_id.in_(ids)

    total_amount = _sum(db, scope)
    item_count = int(db.scalar(select(func.count()).select_from(ExpenseItem).where(scope)) or 0)
    deductible = _sum(db, scope, ExpenseItem.vat_deductible.is_(True))
    non_deductible = _sum(db, scope, ExpenseItem.vat_deductible.is_(False))
    warning_count = int(
        db.scalar(
            select(func.count()).select_from(ExpenseItem).where(
                scope, ExpenseItem.total_amount > 30000, ExpenseItem.evidence_type.in_(_NON_QUALIFIED)
            )
        ) or 0
    )

    status_rows = db.execute(
        select(ExpenseReport.status, func.count()).where(ExpenseReport.id.in_(ids)).group_by(ExpenseReport.status)
    ).all()
    status_counts = {(s.value if hasattr(s, "value") else str(s)): c for s, c in status_rows}

    acct_name = func.coalesce(Account.name, _MISC)
    acct_rows = db.execute(
        select(acct_name, func.sum(ExpenseItem.total_amount), func.count())
        .select_from(ExpenseItem)
        .join(Account, ExpenseItem.account_id == Account.id, isouter=True)
        .where(scope)
        .group_by(acct_name)
        .order_by(func.sum(ExpenseItem.total_amount).desc())
    ).all()
    by_account = [NamedAmount(name=n, amount=int(a or 0), count=c) for n, a, c in acct_rows][:8]

    dept_name = func.coalesce(ExpenseItem.dept_snapshot, _MISC)
    dept_rows = db.execute(
        select(dept_name, func.sum(ExpenseItem.total_amount))
        .where(scope)
        .group_by(dept_name)
        .order_by(func.sum(ExpenseItem.total_amount).desc())
    ).all()
    by_dept = [NamedAmount(name=n, amount=int(a or 0)) for n, a in dept_rows][:8]

    month_rows = db.execute(
        select(ExpenseReport.period, func.sum(ExpenseItem.total_amount))
        .select_from(ExpenseItem)
        .join(ExpenseReport, ExpenseItem.report_id == ExpenseReport.id)
        .where(scope)
        .group_by(ExpenseReport.period)
        .order_by(ExpenseReport.period)
    ).all()
    by_month = [MonthAmount(period=p, amount=int(a or 0)) for p, a in month_rows][-6:]

    return DashboardStats(
        total_amount=total_amount,
        item_count=item_count,
        report_count=len(ids),
        status_counts=status_counts,
        deductible_amount=deductible,
        non_deductible_amount=non_deductible,
        warning_count=warning_count,
        by_account=by_account,
        by_dept=by_dept,
        by_month=by_month,
    )
