from conftest import ADMIN, EMPLOYEE, MANAGER


def _create_and_submit(client, auth, accounts):
    payload = {
        "title": "워크플로우 경비",
        "period": "2026-07",
        "items": [
            {"tx_date": "2026-07-02", "total_amount": 5000, "account_id": accounts["복리후생비"],
             "vendor_name": "스타벅스", "evidence_type": "card", "pay_method": "corporate_card"},
        ],
    }
    rid = client.post("/api/v1/expenses/reports", headers=auth(EMPLOYEE), json=payload).json()["id"]
    client.post(f"/api/v1/expenses/reports/{rid}/submit", headers=auth(EMPLOYEE))
    return rid


def test_full_workflow(client, auth, accounts):
    """제출 → 팀장승인 → 검토완료 → 마감 → 엑셀 다운로드."""
    rid = _create_and_submit(client, auth, accounts)

    r = client.post(f"/api/v1/approvals/{rid}/approve", headers=auth(MANAGER), json={})
    assert r.status_code == 200 and r.json()["status"] == "team_approved"

    r = client.post(f"/api/v1/approvals/{rid}/review", headers=auth(ADMIN), json={})
    assert r.status_code == 200 and r.json()["status"] == "reviewed"

    r = client.post("/api/v1/closings", headers=auth(ADMIN), json={"period": "2026-07"})
    assert r.status_code == 201
    cid = r.json()["id"]
    assert r.json()["export_key"]

    # 마감 후 신청서 잠금
    assert client.get(f"/api/v1/expenses/reports/{rid}", headers=auth(ADMIN)).json()["status"] == "closed"

    # 엑셀 다운로드
    r = client.get(f"/api/v1/closings/{cid}/download", headers=auth(ADMIN))
    assert r.status_code == 200
    assert "spreadsheet" in r.headers["content-type"]
    assert len(r.content) > 0


def test_employee_cannot_approve(client, auth, accounts):
    rid = _create_and_submit(client, auth, accounts)
    r = client.post(f"/api/v1/approvals/{rid}/approve", headers=auth(EMPLOYEE), json={})
    assert r.status_code == 403


def test_reject_returns_to_editable(client, auth, accounts):
    rid = _create_and_submit(client, auth, accounts)
    r = client.post(f"/api/v1/approvals/{rid}/reject", headers=auth(MANAGER), json={"comment": "재작성 요망"})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    # 반려 후 다시 제출 가능
    r = client.post(f"/api/v1/expenses/reports/{rid}/submit", headers=auth(EMPLOYEE))
    assert r.status_code == 200 and r.json()["status"] == "submitted"


def test_reject_requires_comment(client, auth, accounts):
    rid = _create_and_submit(client, auth, accounts)
    r = client.post(f"/api/v1/approvals/{rid}/reject", headers=auth(MANAGER), json={})
    assert r.status_code == 422  # comment 필수


def test_close_without_reviewed_fails(client, auth, accounts):
    # 검토완료 건이 없으면 마감 불가
    _create_and_submit(client, auth, accounts)  # submitted 상태에 머무름
    r = client.post("/api/v1/closings", headers=auth(ADMIN), json={"period": "2026-07"})
    assert r.status_code == 400


def test_report_history_records_actions(client, auth, accounts):
    rid = _create_and_submit(client, auth, accounts)
    client.post(f"/api/v1/approvals/{rid}/reject", headers=auth(MANAGER), json={"comment": "금액 재확인 필요"})
    hist = client.get(f"/api/v1/expenses/reports/{rid}/history", headers=auth(EMPLOYEE)).json()
    assert [h["action"] for h in hist] == ["submit", "reject"]  # 시간순
    reject = hist[-1]
    assert reject["comment"] == "금액 재확인 필요"
    assert reject["actor_name"] == "김팀장"


def test_history_includes_close(client, auth, accounts):
    rid = _create_and_submit(client, auth, accounts)
    client.post(f"/api/v1/approvals/{rid}/approve", headers=auth(MANAGER), json={})
    client.post(f"/api/v1/approvals/{rid}/review", headers=auth(ADMIN), json={})
    client.post("/api/v1/closings", headers=auth(ADMIN), json={"period": "2026-07"})
    hist = client.get(f"/api/v1/expenses/reports/{rid}/history", headers=auth(ADMIN)).json()
    assert [h["action"] for h in hist] == ["submit", "approve", "review", "close"]


def test_role_based_report_visibility(client, auth, accounts):
    """직원은 본인 것만 조회."""
    _create_and_submit(client, auth, accounts)
    emp_reports = client.get("/api/v1/expenses/reports", headers=auth(EMPLOYEE)).json()
    assert len(emp_reports) == 1
    # 관리자는 전사 조회
    admin_reports = client.get("/api/v1/expenses/reports", headers=auth(ADMIN)).json()
    assert len(admin_reports) == 1
