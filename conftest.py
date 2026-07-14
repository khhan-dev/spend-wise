"""pytest 공통 설정: 격리된 테스트 DB + 시드 + 인증 헬퍼."""

import os

# app 임포트 전에 테스트용 환경변수 설정
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ENVIRONMENT"] = "test"  # lifespan의 create_all 스킵(픽스처가 담당)
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-bytes-long!!"
os.environ["UPLOAD_DIR"] = "storage/_test_uploads"  # 테스트 전용 증빙 저장소

import shutil

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from scripts.seed import run as seed_run

_TEST_UPLOAD_DIR = "storage/_test_uploads"

DEFAULT_PW = "test1234"
ADMIN = "admin@company.com"
MANAGER = "manager@company.com"
EMPLOYEE = "employee@company.com"


@pytest.fixture(autouse=True)
def db():
    """각 테스트마다 스키마 재생성 + 시드 + 증빙 저장소 초기화로 완전 격리."""
    Base.metadata.drop_all(engine)
    shutil.rmtree(_TEST_UPLOAD_DIR, ignore_errors=True)
    seed_run()  # create_all + 계정과목/조직/사용자 시드
    yield
    Base.metadata.drop_all(engine)
    shutil.rmtree(_TEST_UPLOAD_DIR, ignore_errors=True)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    """이메일로 로그인해 Authorization 헤더를 반환하는 헬퍼."""

    def _login(email: str = EMPLOYEE, password: str = DEFAULT_PW) -> dict:
        res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    return _login


@pytest.fixture
def accounts(client, auth):
    """계정과목명 → id 매핑."""
    res = client.get("/api/v1/accounts", headers=auth(EMPLOYEE))
    return {a["name"]: a["id"] for a in res.json()}
