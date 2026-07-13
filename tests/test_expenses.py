import io

from conftest import EMPLOYEE, MANAGER


def _report_payload(accounts, **over):
    base = {
        "title": "테스트 경비",
        "period": "2026-07",
        "items": [
            {
                "tx_date": "2026-07-02",
                "total_amount": 5000,
                "account_id": accounts["복리후생비"],
                "vendor_name": "스타벅스",
                "evidence_type": "card",
                "pay_method": "corporate_card",
            }
        ],
    }
    base.update(over)
    return base


def _create(client, auth, accounts, **over):
    res = client.post("/api/v1/expenses/reports", headers=auth(EMPLOYEE), json=_report_payload(accounts, **over))
    assert res.status_code == 201, res.text
    return res.json()


def test_create_auto_split_and_deductible(client, auth, accounts):
    """카드 5,000원 → 공급 4,545 + 부가 455, 공제 대상 계정이면 공제."""
    report = _create(client, auth, accounts)
    item = report["items"][0]
    assert item["supply_amount"] == 4545
    assert item["vat_amount"] == 455
    assert item["vat_deductible"] is True
    assert item["vendor_name"] == "스타벅스"


def test_entertainment_not_deductible(client, auth, accounts):
    """기업업무추진비(접대비)는 불공제."""
    report = _create(
        client,
        auth,
        accounts,
        items=[
            {
                "tx_date": "2026-07-05",
                "total_amount": 100000,
                "account_id": accounts["기업업무추진비"],
                "evidence_type": "card",
                "pay_method": "corporate_card",
            }
        ],
    )
    assert report["items"][0]["vat_deductible"] is False


def test_dept_team_snapshot(client, auth, accounts):
    """신청자 소속이 자동 배부된다."""
    report = _create(client, auth, accounts)
    item = report["items"][0]
    assert item["dept_snapshot"] == "경영지원본부"
    assert item["team_snapshot"] == "총무팀"


def test_simple_receipt_no_vat(client, auth, accounts):
    """간이영수증은 전액 공급가액, 부가세 0."""
    report = _create(
        client,
        auth,
        accounts,
        items=[
            {
                "tx_date": "2026-07-08",
                "total_amount": 8000,
                "account_id": accounts["복리후생비"],
                "evidence_type": "simple_receipt",
                "pay_method": "personal_card",
            }
        ],
    )
    item = report["items"][0]
    assert item["supply_amount"] == 8000 and item["vat_amount"] == 0
    assert item["vat_deductible"] is False


def test_validation_rules(client, auth, accounts):
    """규칙 A(3만원 초과 비적격 경고) + 규칙 D(금액 일치)."""
    report = _create(
        client,
        auth,
        accounts,
        items=[
            {"tx_date": "2026-07-12", "total_amount": 40000, "account_id": accounts["소모품비"],
             "evidence_type": "simple_receipt", "pay_method": "personal_card"},
        ],
    )
    res = client.get(f"/api/v1/expenses/reports/{report['id']}/validate", headers=auth(EMPLOYEE))
    val = res.json()[0]
    assert val["evidence_warning"] is not None  # 3만원 초과 간이영수증
    assert val["amount_ok"] is True


def test_update_report(client, auth, accounts):
    report = _create(client, auth, accounts)
    payload = _report_payload(accounts, title="수정됨", period="2026-08")
    payload["items"][0]["total_amount"] = 11000
    res = client.put(f"/api/v1/expenses/reports/{report['id']}", headers=auth(EMPLOYEE), json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "수정됨" and body["period"] == "2026-08"
    assert body["items"][0]["supply_amount"] == 10000 and body["items"][0]["vat_amount"] == 1000


def test_update_forbidden_for_other_user(client, auth, accounts):
    report = _create(client, auth, accounts)
    res = client.put(
        f"/api/v1/expenses/reports/{report['id']}",
        headers=auth(MANAGER),
        json=_report_payload(accounts),
    )
    assert res.status_code == 403


def test_update_blocked_after_submit(client, auth, accounts):
    report = _create(client, auth, accounts)
    client.post(f"/api/v1/expenses/reports/{report['id']}/submit", headers=auth(EMPLOYEE))
    res = client.put(
        f"/api/v1/expenses/reports/{report['id']}",
        headers=auth(EMPLOYEE),
        json=_report_payload(accounts),
    )
    assert res.status_code == 409


def test_delete_report(client, auth, accounts):
    report = _create(client, auth, accounts)
    res = client.delete(f"/api/v1/expenses/reports/{report['id']}", headers=auth(EMPLOYEE))
    assert res.status_code == 204
    assert client.get(f"/api/v1/expenses/reports/{report['id']}", headers=auth(EMPLOYEE)).status_code == 404


def test_ocr_stub_requires_manual(client, auth):
    files = {"file": ("r.jpg", io.BytesIO(b"fake"), "image/jpeg")}
    res = client.post("/api/v1/receipts/ocr", headers=auth(EMPLOYEE), files=files)
    assert res.status_code == 200
    assert res.json()["manual_input_required"] is True
