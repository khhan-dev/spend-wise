"""증빙 이미지 저장·첨부·서빙·ZIP 테스트."""

import io

from conftest import ADMIN, EMPLOYEE
from app.services.storage import get_storage


def _upload(client, auth):
    files = {"file": ("r.png", io.BytesIO(b"FAKE-PNG-BYTES"), "image/png")}
    res = client.post("/api/v1/receipts/ocr", headers=auth(EMPLOYEE), files=files)
    assert res.status_code == 200, res.text
    return res.json()


def _report_with_image(client, auth, accounts, image_key):
    payload = {
        "title": "증빙 테스트",
        "period": "2026-07",
        "items": [
            {"tx_date": "2026-07-02", "total_amount": 5000, "account_id": accounts["복리후생비"],
             "evidence_type": "card", "pay_method": "corporate_card", "image_key": image_key},
        ],
    }
    res = client.post("/api/v1/expenses/reports", headers=auth(EMPLOYEE), json=payload)
    assert res.status_code == 201, res.text
    return res.json()


# ── 스토리지 유닛 ────────────────────────────────
def test_storage_save_and_load():
    storage = get_storage()
    key = storage.save(b"hello", "png")
    assert storage.exists(key)
    assert storage.load(key) == b"hello"


def test_storage_rejects_path_traversal():
    storage = get_storage()
    assert storage.exists("../secret") is False
    assert storage.exists("sub/dir.png") is False
    assert storage.exists("") is False


# ── 업로드 & 첨부 ────────────────────────────────
def test_upload_saves_image_and_returns_key(client, auth):
    body = _upload(client, auth)
    assert body["image_key"]
    assert get_storage().exists(body["image_key"])
    # CLOVA 미설정 → 스텁 → 수동 입력 필요
    assert body["manual_input_required"] is True


def test_item_attaches_receipt(client, auth, accounts):
    key = _upload(client, auth)["image_key"]
    report = _report_with_image(client, auth, accounts, key)
    item = report["items"][0]
    assert item["image_key"] == key


def test_bogus_image_key_not_attached(client, auth, accounts):
    report = _report_with_image(client, auth, accounts, "does-not-exist.png")
    assert report["items"][0]["image_key"] is None


def test_image_served_to_owner(client, auth, accounts):
    key = _upload(client, auth)["image_key"]
    item = _report_with_image(client, auth, accounts, key)["items"][0]
    res = client.get(f"/api/v1/receipts/{item['id']}/image", headers=auth(EMPLOYEE))
    assert res.status_code == 200
    assert res.content == b"FAKE-PNG-BYTES"


def test_image_forbidden_for_unrelated_user(client, auth, accounts):
    # 다른 팀 소속 없는 직원 생성
    client.post(
        "/api/v1/users",
        headers=auth(ADMIN),
        json={"name": "타부서", "email": "other@company.com", "password": "test1234", "role": "employee"},
    )
    key = _upload(client, auth)["image_key"]
    item = _report_with_image(client, auth, accounts, key)["items"][0]
    res = client.get(f"/api/v1/receipts/{item['id']}/image", headers=auth("other@company.com"))
    assert res.status_code == 403


def test_image_404_when_no_receipt(client, auth, accounts):
    report = _report_with_image(client, auth, accounts, None)
    item = report["items"][0]
    assert item["image_key"] is None
    res = client.get(f"/api/v1/receipts/{item['id']}/image", headers=auth(EMPLOYEE))
    assert res.status_code == 404


# ── 마감 증빙 ZIP ────────────────────────────────
def _run_to_closed(client, auth, accounts, image_key):
    from conftest import MANAGER

    report = _report_with_image(client, auth, accounts, image_key)
    rid = report["id"]
    client.post(f"/api/v1/expenses/reports/{rid}/submit", headers=auth(EMPLOYEE))
    client.post(f"/api/v1/approvals/{rid}/approve", headers=auth(MANAGER), json={})
    client.post(f"/api/v1/approvals/{rid}/review", headers=auth(ADMIN), json={})
    return client.post("/api/v1/closings", headers=auth(ADMIN), json={"period": "2026-07"}).json()


def test_closing_receipts_zip(client, auth, accounts):
    key = _upload(client, auth)["image_key"]
    closing = _run_to_closed(client, auth, accounts, key)
    res = client.get(f"/api/v1/closings/{closing['id']}/receipts-zip", headers=auth(ADMIN))
    assert res.status_code == 200
    assert res.content[:2] == b"PK"  # zip 시그니처


def test_closing_receipts_zip_404_when_no_images(client, auth, accounts):
    closing = _run_to_closed(client, auth, accounts, None)  # 증빙 없음
    res = client.get(f"/api/v1/closings/{closing['id']}/receipts-zip", headers=auth(ADMIN))
    assert res.status_code == 404
