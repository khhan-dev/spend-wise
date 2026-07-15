"""대시보드 집계 통계 테스트."""

from conftest import ADMIN, EMPLOYEE, MANAGER


def _seed_expenses(client, auth, accounts):
    payload = {
        "title": "통계용",
        "period": "2026-07",
        "items": [
            {"tx_date": "2026-07-02", "total_amount": 11000, "account_id": accounts["복리후생비"],
             "evidence_type": "card", "pay_method": "corporate_card"},
            {"tx_date": "2026-07-05", "total_amount": 40000, "account_id": accounts["소모품비"],
             "evidence_type": "simple_receipt", "pay_method": "personal_card"},  # 3만원 초과 비적격 → 경고
            {"tx_date": "2026-07-09", "total_amount": 22000, "account_id": accounts["기업업무추진비"],
             "evidence_type": "card", "pay_method": "corporate_card"},  # 불공제
        ],
    }
    return client.post("/api/v1/expenses/reports", headers=auth(EMPLOYEE), json=payload).json()


def test_dashboard_empty(client, auth):
    stats = client.get("/api/v1/stats/dashboard", headers=auth(EMPLOYEE)).json()
    assert stats["total_amount"] == 0
    assert stats["by_account"] == []
    assert stats["by_month"] == []


def test_dashboard_aggregates(client, auth, accounts):
    _seed_expenses(client, auth, accounts)
    stats = client.get("/api/v1/stats/dashboard", headers=auth(EMPLOYEE)).json()

    assert stats["total_amount"] == 73000
    assert stats["item_count"] == 3
    assert stats["report_count"] == 1
    assert stats["warning_count"] == 1  # 40,000 간이영수증

    # 계정과목별 집계 (금액 내림차순)
    by_acct = {a["name"]: a["amount"] for a in stats["by_account"]}
    assert by_acct["소모품비"] == 40000
    assert by_acct["기업업무추진비"] == 22000
    assert by_acct["복리후생비"] == 11000
    assert stats["by_account"][0]["name"] == "소모품비"  # 최대

    # 부서별 집계
    assert stats["by_dept"][0]["name"] == "경영지원본부"
    assert stats["by_dept"][0]["amount"] == 73000

    # 월별 추이
    assert stats["by_month"] == [{"period": "2026-07", "amount": 73000}]

    # 공제/불공제 (복리후생비 card=공제 10000+1000=11000 공제 / 소모품비 간이=불공제 / 접대비=불공제)
    assert stats["deductible_amount"] == 11000
    assert stats["non_deductible_amount"] == 62000

    # 상태 분포
    assert stats["status_counts"].get("draft") == 1


def test_dashboard_scoped_by_role(client, auth, accounts):
    _seed_expenses(client, auth, accounts)  # employee 소유
    # 관리자는 전사 → 집계에 포함
    admin_stats = client.get("/api/v1/stats/dashboard", headers=auth(ADMIN)).json()
    assert admin_stats["total_amount"] == 73000
    # 팀장(같은 팀)도 조회 가능
    mgr_stats = client.get("/api/v1/stats/dashboard", headers=auth(MANAGER)).json()
    assert mgr_stats["total_amount"] == 73000


def test_dashboard_requires_auth(client):
    assert client.get("/api/v1/stats/dashboard").status_code == 401
