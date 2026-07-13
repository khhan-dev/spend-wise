# 경비처리 웹서비스 (백엔드 MVP)

경영지원실이 회사 경비를 수집·분류·승인·마감하고, **클릭 한 번으로 세무 신고용 엑셀**을 생성하는 사내 시스템의 백엔드.

- **스택**: FastAPI · SQLAlchemy 2.0 · PostgreSQL · JWT · openpyxl
- **배포 타깃**: AWS 서울 리전 (ECS Fargate · RDS · S3)
- **제외(보류)**: 홈택스·카드사 자동수집(수집 벤더) 연동 — 추후 결정

관련 설계 문서: 기능명세서 / 데이터모델(ERD) / 아키텍처 (Artifact).

---

## 빠른 시작 (로컬 · SQLite)

```bash
# 1) 가상환경 & 의존성
python -m venv .venv
.venv\Scripts\activate            # (Windows PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

# 2) 환경파일
copy .env.example .env            # (bash: cp .env.example .env)

# 3) 초기 데이터 시드(계정과목·조직·계정)
python -m scripts.seed

# 4) 서버 실행
uvicorn app.main:app --reload
```

- API 문서(Swagger): http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

기본 계정 (비밀번호 `test1234`):

| 이메일 | 역할 |
|---|---|
| admin@company.com | 경영지원실(관리자) |
| manager@company.com | 팀장 |
| employee@company.com | 일반 직원 |

## 운영 (PostgreSQL · Docker)

```bash
docker compose up --build
```

`.env` 의 `DATABASE_URL` 을 RDS(PostgreSQL)로 바꾸고, 마이그레이션을 적용한다:

```bash
alembic revision --autogenerate -m "init"   # 최초 1회 스키마 생성
alembic upgrade head
```

> dev 환경(`ENVIRONMENT=dev`)에서는 서버 기동 시 테이블을 자동 생성한다. 운영에서는 Alembic 마이그레이션을 사용한다.

---

## 핵심 흐름 (API)

```
직원   POST /api/v1/expenses/reports            경비 신청서 작성(소속 자동배부)
       POST /api/v1/receipts/ocr               영수증 OCR 초안(현재 스텁→수동입력)
       POST /api/v1/expenses/reports/{id}/submit  제출
팀장   POST /api/v1/approvals/{id}/approve      승인
       POST /api/v1/approvals/{id}/reject       반려(사유 필수)
관리자 POST /api/v1/approvals/{id}/review       검토완료
       POST /api/v1/closings                    월 마감 + 엑셀 생성
       GET  /api/v1/closings/{id}/download      엑셀 다운로드
```

경비 상태: `작성중 → 제출 → 팀장승인 → 검토완료 → 마감` (반려 시 작성중 복귀)

## 도메인 규칙 (자동 적용)

- 금액 자동 분리: 적격+과세 증빙은 공급가액/부가세 분리, 면세·간이는 전액 공급가액
- 부가세 공제: 적격+과세 증빙 & 공제대상 계정일 때만 공제
- 규칙 A: 3만원 초과 비적격 증빙 → 경고 (`/validate`)
- 규칙 D: 공급가액 + 부가세 = 합계 검증 (`/validate`)

## 프로젝트 구조

```
app/
  core/        설정 · DB · 보안(JWT/해시)
  models/      SQLAlchemy 모델(ERD) · enum
  schemas/     Pydantic 입출력 스키마
  api/v1/      라우터(auth·users·accounts·expenses·approvals·closings·receipts)
  services/    도메인 규칙 · OCR(스텁) · 엑셀 생성
scripts/seed.py   초기 데이터
alembic/          마이그레이션
```

## OCR 연동 (다음 작업)

`app/services/ocr.py` 의 `StubOcrProvider` 를 `ClovaOcrProvider` 로 교체하면 된다.
현재는 항상 실패를 반환해 프론트가 **수동 입력 폴백**으로 동작한다.
