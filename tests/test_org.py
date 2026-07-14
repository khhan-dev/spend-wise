"""조직(부서/팀) · 사용자 관리 테스트."""

from conftest import ADMIN, EMPLOYEE


def test_org_tree(client, auth):
    res = client.get("/api/v1/org", headers=auth(ADMIN))
    assert res.status_code == 200
    tree = res.json()
    assert tree["name"] == "샘플주식회사"
    assert any(d["name"] == "경영지원본부" for d in tree["departments"])
    dept = next(d for d in tree["departments"] if d["name"] == "경영지원본부")
    assert any(t["name"] == "총무팀" for t in dept["teams"])


def test_org_requires_admin(client, auth):
    assert client.get("/api/v1/org", headers=auth(EMPLOYEE)).status_code == 403


def test_create_and_delete_department(client, auth):
    res = client.post("/api/v1/departments", headers=auth(ADMIN), json={"name": "영업본부", "code": "SALES"})
    assert res.status_code == 201
    dept_id = res.json()["id"]
    # 팀 없는 부서는 삭제 가능
    assert client.delete(f"/api/v1/departments/{dept_id}", headers=auth(ADMIN)).status_code == 204


def test_cannot_delete_department_with_teams(client, auth):
    dept = client.post("/api/v1/departments", headers=auth(ADMIN), json={"name": "개발본부"}).json()
    client.post("/api/v1/teams", headers=auth(ADMIN), json={"department_id": dept["id"], "name": "플랫폼팀"})
    res = client.delete(f"/api/v1/departments/{dept['id']}", headers=auth(ADMIN))
    assert res.status_code == 409


def test_create_team_and_appears_in_tree(client, auth):
    dept = client.post("/api/v1/departments", headers=auth(ADMIN), json={"name": "개발본부"}).json()
    team = client.post("/api/v1/teams", headers=auth(ADMIN), json={"department_id": dept["id"], "name": "데이터팀"})
    assert team.status_code == 201
    tree = client.get("/api/v1/org", headers=auth(ADMIN)).json()
    d = next(d for d in tree["departments"] if d["id"] == dept["id"])
    assert any(t["name"] == "데이터팀" for t in d["teams"])


def test_cannot_delete_team_with_users(client, auth):
    # 총무팀에는 시드 사용자가 있음
    tree = client.get("/api/v1/org", headers=auth(ADMIN)).json()
    team_id = next(t["id"] for d in tree["departments"] for t in d["teams"] if t["name"] == "총무팀")
    res = client.delete(f"/api/v1/teams/{team_id}", headers=auth(ADMIN))
    assert res.status_code == 409


def test_update_user_role_and_team(client, auth):
    users = client.get("/api/v1/users", headers=auth(ADMIN)).json()
    emp = next(u for u in users if u["email"] == EMPLOYEE)
    # 역할 변경
    r = client.patch(f"/api/v1/users/{emp['id']}", headers=auth(ADMIN), json={"role": "manager"})
    assert r.status_code == 200 and r.json()["role"] == "manager"
    # 팀 해제
    r = client.patch(f"/api/v1/users/{emp['id']}", headers=auth(ADMIN), json={"team_id": None})
    assert r.json()["team_id"] is None
    # 비활성화
    r = client.patch(f"/api/v1/users/{emp['id']}", headers=auth(ADMIN), json={"is_active": False})
    assert r.json()["is_active"] is False


def test_user_management_requires_admin(client, auth):
    assert client.get("/api/v1/users", headers=auth(EMPLOYEE)).status_code == 403
    assert client.post("/api/v1/departments", headers=auth(EMPLOYEE), json={"name": "x"}).status_code == 403
