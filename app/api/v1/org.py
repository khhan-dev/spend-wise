import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import Company, Department, Role, Team, User
from app.schemas.org import (
    CompanyTree,
    DepartmentCreate,
    DepartmentOut,
    TeamCreate,
    TeamOut,
)

router = APIRouter(tags=["org"])


def _first_company(db: Session) -> Company:
    company = db.scalar(select(Company).order_by(Company.created_at))
    if company is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="회사 정보가 없습니다. 먼저 시드를 실행하세요.")
    return company


# ── 조직 트리 ────────────────────────────────────
@router.get("/org", response_model=CompanyTree)
def org_tree(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.admin))):
    """회사 > 부서 > 팀 트리 (관리 화면·배정 드롭다운용)."""
    return _first_company(db)


# ── 부서 ─────────────────────────────────────────
@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    company = _first_company(db)
    dept = Department(company_id=company.id, name=body.name, code=body.code)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    dept = db.get(Department, department_id)
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="부서를 찾을 수 없습니다.")
    if dept.teams:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="소속 팀이 있어 삭제할 수 없습니다. 팀을 먼저 삭제하세요.")
    db.delete(dept)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── 팀 ───────────────────────────────────────────
@router.post("/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    body: TeamCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    if db.get(Department, body.department_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="부서를 찾을 수 없습니다.")
    team = Team(department_id=body.department_id, name=body.name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="팀을 찾을 수 없습니다.")
    if db.scalar(select(User).where(User.team_id == team_id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="소속 직원이 있어 삭제할 수 없습니다.")
    db.delete(team)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
