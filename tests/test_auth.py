from conftest import ADMIN, EMPLOYEE


def test_login_success(client):
    res = client.post("/api/v1/auth/login", data={"username": EMPLOYEE, "password": "test1234"})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    res = client.post("/api/v1/auth/login", data={"username": EMPLOYEE, "password": "wrong"})
    assert res.status_code == 401


def test_me(client, auth):
    res = client.get("/api/v1/auth/me", headers=auth(EMPLOYEE))
    assert res.status_code == 200
    assert res.json()["email"] == EMPLOYEE
    assert res.json()["role"] == "employee"


def test_refresh(client):
    tokens = client.post("/api/v1/auth/login", data={"username": ADMIN, "password": "test1234"}).json()
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_refresh_rejects_access_token(client):
    tokens = client.post("/api/v1/auth/login", data={"username": ADMIN, "password": "test1234"}).json()
    # access 토큰을 refresh로 사용하면 거부
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert res.status_code == 401


def test_protected_requires_auth(client):
    assert client.get("/api/v1/accounts").status_code == 401


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
