"""신청서 열람 권한 공통 규칙 (직원=본인 / 팀장=소속 팀 / 관리자=전사)."""

from app.models import ExpenseReport, Role, User


def can_view_report(user: User, report: ExpenseReport) -> bool:
    if user.role == Role.admin or report.user_id == user.id:
        return True
    if user.role == Role.manager and user.team_id and report.user.team_id == user.team_id:
        return True
    return False
