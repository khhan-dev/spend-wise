from pydantic import BaseModel


class NamedAmount(BaseModel):
    name: str
    amount: int
    count: int | None = None


class MonthAmount(BaseModel):
    period: str
    amount: int


class DashboardStats(BaseModel):
    total_amount: int
    item_count: int
    report_count: int
    status_counts: dict[str, int]
    deductible_amount: int
    non_deductible_amount: int
    warning_count: int  # 3만원 초과 비적격 증빙 건수
    by_account: list[NamedAmount]
    by_dept: list[NamedAmount]
    by_month: list[MonthAmount]
