# 경비처리 웹서비스 (Expense Management)

회사 경영지원실의 **월간 경비 처리 → 세무 신고 자료 생성**을 자동화하는 사내 웹서비스입니다.
직원이 영수증을 올리면 **OCR로 항목을 자동 인식**하고, 소속 부서/팀으로 자동 분류하며, 승인 워크플로우를 거쳐
**클릭 한 번으로 세무대리인 전달용 엑셀 + 증빙 ZIP**을 생성합니다.

> 이 저장소는 포트폴리오/면접 공유용으로 정리되었습니다. 실제 자격증명(CLOVA 키 등)은 포함되어 있지 않으며,
> 로컬 `.env`로만 주입되고 git에는 올라가지 않습니다.

---

## 핵심 특징

- 🧾 **적격증빙 중심 설계** — 세금계산서·계산서·신용카드·현금영수증(적격) vs 간이영수증(비적격)을 구분하고, **3만원 초과 비적격 경고**·**부가세 매입세액공제 자동 판정**·**공급가액/부가세 자동 분리** 규칙을 내장
- 📷 **영수증 OCR** — Naver CLOVA OCR 실연동(General/Receipt 응답 모두 파싱). 미설정/실패 시 자동으로 수동 입력 폴백
- 🏢 **조직 자동 분류** — 로그인 사용자의 부서/팀으로 경비 자동 배부(등록 시점 스냅샷)
- ✅ **승인 워크플로우** — 작성중 → 제출 → 팀장 승인 → 검토 완료 → 마감 (반려 지원), 전 과정 이력 타임라인
- 📎 **증빙 보관** — 원본 이미지 저장·첨부·조회, 마감 시 증빙 ZIP 동봉 (세법상 5년 보관 대응)
- 📊 **원클릭 산출물** — 월 마감 시 경비내역·부서/팀별·계정과목별·부가세 정리 5개 시트 엑셀 자동 생성
- 🔐 **역할 기반 접근제어(RBAC)** — 직원 / 팀장 / 경영지원실(관리자) 3역할, JWT 인증

## 기술 스택

| 영역 | 스택 |
|---|---|
| 백엔드 | Python 3.12 · **FastAPI** · SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| 프론트엔드 | **React 18** · TypeScript · Vite · Tailwind CSS · TanStack Query · React Router |
| 데이터베이스 | PostgreSQL(운영) / SQLite(개발) |
| 인증 | JWT (Access + Refresh) · RBAC |
| OCR | Naver CLOVA OCR (httpx 연동) |
| 문서 산출 | openpyxl (엑셀), zipfile (증빙 ZIP) |
| 배포 타깃 | AWS 서울 리전 (ECS Fargate · RDS · S3) |
| 테스트 | pytest (55 케이스) |

## 문서

| 문서 | 설명 |
|---|---|
| [요구사항명세서](docs/requirements.md) | 배경·사용자·기능/비기능 요구사항·도메인 규칙·범위 |
| [상세설계서](docs/design.md) | 아키텍처·데이터 모델(ERD)·API 명세·상태 흐름·보안 |
| [사용설명서](docs/setup.md) | 설치·환경설정·실행·CLOVA OCR 연동·테스트·배포 |

---

## 빠른 시작 (로컬 · SQLite)

사전 요구사항: **Python 3.12+**, **Node.js 20+**

### 1) 백엔드

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # (bash: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env             # (bash: cp .env.example .env)
python -m scripts.seed             # 계정과목·조직·데모 계정 시드
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

### 2) 프론트엔드

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

### 데모 계정 (비밀번호 `test1234`)

| 이메일 | 역할 |
|---|---|
| admin@company.com | 경영지원실(관리자) |
| manager@company.com | 팀장 |
| employee@company.com | 일반 직원 |

자세한 설정(CLOVA OCR 연동, Docker, 마이그레이션 등)은 [사용설명서](docs/setup.md)를 참고하세요.

---

## 프로젝트 구조

```
.
├── app/                     # FastAPI 백엔드
│   ├── core/                # 설정 · DB · 보안(JWT/해시)
│   ├── models/              # SQLAlchemy 모델(ERD) · enum
│   ├── schemas/             # Pydantic 입출력 스키마
│   ├── api/v1/              # 라우터(auth·users·org·accounts·expenses·approvals·closings·receipts)
│   └── services/            # 도메인 규칙 · OCR · 스토리지 · 엑셀 · 권한
├── frontend/                # React + Vite + Tailwind SPA
│   └── src/{pages,components,lib,auth}
├── alembic/                 # DB 마이그레이션
├── scripts/seed.py          # 초기 데이터
├── tests/                   # pytest (55)
└── docs/                    # 요구사항·설계·사용 문서
```

## 테스트

```bash
pip install -r requirements-dev.txt
pytest                        # 55 케이스 (인증·경비·워크플로우·OCR·증빙·조직)
```

## 범위 (의도적 제외)

- **홈택스·카드사 자동수집(스크래핑 벤더 연동)** 은 범위에서 제외했습니다. 대신 최종 산출물을
  **세무대리인 전달용 엑셀 + 증빙 ZIP** 으로 만들어, 실무에서 가장 흔한 "세무사에게 넘기는 흐름"을 구현했습니다.

---

<sub>본 프로젝트는 한국 세무 실무(적격증빙·부가가치세·경비 처리) 리서치를 바탕으로 설계되었습니다.</sub>
