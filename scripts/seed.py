"""초기 데이터 시드: 계정과목, 샘플 조직, 관리자/팀장/직원 계정.

실행:  python -m scripts.seed
"""

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Account, Company, Department, Role, Team, User

# (계정과목명, 부가세 공제 기본값)
ACCOUNTS = [
    ("복리후생비", True),
    ("여비교통비", True),
    ("소모품비", True),
    ("통신비", True),
    ("도서인쇄비", True),
    ("지급수수료", True),
    ("기업업무추진비", False),  # 접대비 → 불공제
    ("차량유지비", False),      # 비영업용 승용차 → 불공제
]

USERS = [
    ("관리자", "admin@company.com", Role.admin),
    ("김팀장", "manager@company.com", Role.manager),
    ("이사원", "employee@company.com", Role.employee),
]
DEFAULT_PW = "test1234"


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 계정과목
        for name, deductible in ACCOUNTS:
            if not db.scalar(select(Account).where(Account.name == name)):
                db.add(Account(name=name, default_deductible=deductible))

        # 조직: 회사 > 부서 > 팀
        company = db.scalar(select(Company)) or Company(name="샘플주식회사", biz_no="123-45-67890")
        db.add(company)
        db.flush()

        dept = db.scalar(select(Department).where(Department.name == "경영지원본부"))
        if not dept:
            dept = Department(company_id=company.id, name="경영지원본부", code="MG")
            db.add(dept)
            db.flush()

        team = db.scalar(select(Team).where(Team.name == "총무팀"))
        if not team:
            team = Team(department_id=dept.id, name="총무팀")
            db.add(team)
            db.flush()

        # 사용자
        for name, email, role in USERS:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(
                    User(
                        name=name,
                        email=email,
                        hashed_password=hash_password(DEFAULT_PW),
                        role=role,
                        team_id=team.id,
                    )
                )

        db.commit()
        print("✓ 시드 완료")
        print(f"  로그인: admin@company.com / manager@company.com / employee@company.com  (비밀번호: {DEFAULT_PW})")
    finally:
        db.close()


if __name__ == "__main__":
    run()
