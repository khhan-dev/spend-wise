# 사용설명서 (설치 · 실행 · 운영)

**프로젝트:** 경비처리 웹서비스 · **버전:** 1.0

이 문서는 프로젝트를 로컬에서 구동하고, CLOVA OCR을 연동하고, 테스트/배포하는 방법을 안내합니다.

---

## 1. 사전 요구사항

| 도구 | 버전 | 확인 |
|---|---|---|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| (선택) Docker | 최신 | `docker --version` |
| (선택) PostgreSQL | 16 | 운영/도커 사용 시 |

> Windows·macOS·Linux 모두 동작합니다. 아래 명령은 Windows PowerShell 기준이며, bash는 괄호로 병기합니다.

---

## 2. 백엔드 설치 · 실행 (로컬 · SQLite)

```bash
# 1) 저장소 루트에서 가상환경
python -m venv .venv
.venv\Scripts\Activate.ps1            # (bash: source .venv/bin/activate)

# 2) 의존성
pip install -r requirements.txt

# 3) 환경파일 생성
copy .env.example .env                 # (bash: cp .env.example .env)

# 4) 초기 데이터 시드 (계정과목 · 조직 · 데모 계정)
python -m scripts.seed

# 5) 서버 실행
uvicorn app.main:app --reload
```

- API 문서(Swagger): <http://localhost:8000/docs>
- 헬스체크: <http://localhost:8000/health>

### 데모 계정 (비밀번호 `test1234`)
| 이메일 | 역할 |
|---|---|
| admin@company.com | 경영지원실(관리자) |
| manager@company.com | 팀장 |
| employee@company.com | 일반 직원 |

---

## 3. 환경변수(.env) 설명

| 키 | 기본값 | 설명 |
|---|---|---|
| `ENVIRONMENT` | `dev` | `dev`면 서버 기동 시 테이블 자동 생성 |
| `DATABASE_URL` | `sqlite:///./dev.db` | 운영: `postgresql+psycopg://user:pw@host:5432/db` |
| `JWT_SECRET` | (변경 필수) | JWT 서명 키. **운영은 반드시 긴 랜덤값으로 교체** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access 만료 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | Refresh 만료 |
| `UPLOAD_DIR` | `storage/uploads` | 증빙 이미지 저장 경로(로컬) |
| `EXPORT_DIR` | `storage/exports` | 엑셀 산출물 경로 |
| `CLOVA_OCR_INVOKE_URL` | (빈값) | CLOVA OCR APIGW Invoke URL |
| `CLOVA_OCR_SECRET` | (빈값) | CLOVA OCR Secret(X-OCR-SECRET) |

> ⚠️ `.env`는 **git에 커밋되지 않습니다**(`.gitignore` 포함). 실제 키는 `.env`에만 넣으세요.
> `.env.example`(템플릿)에는 절대 실제 값을 넣지 마세요.

---

## 4. 프론트엔드 설치 · 실행

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

- 백엔드 주소는 `frontend/.env`의 `VITE_API_BASE`로 설정(기본 `http://localhost:8000`).
- 프로덕션 빌드: `npm run build` → `dist/`

---

## 5. CLOVA OCR 연동 (선택)

미설정 시 OCR은 **스텁**으로 동작하여 항상 "수동 입력"으로 폴백합니다. 실제 인식을 켜려면:

1. **Naver Cloud 콘솔 → CLOVA OCR** 에서 **도메인 생성**
   - 지원 언어: **한국어**, 서비스 타입: **일반(General)** (영수증은 양식이 다양)
2. **API Gateway 이용 신청**(상품 활성화) 후, 해당 도메인에서 **[자동 연동]** 실행
   - → 공개 **Invoke URL** 발급: `https://<id>.apigw.ntruss.com/custom/v1/.../general`
3. 같은 화면에서 **Secret Key** 생성
4. `.env`에 입력(따옴표·`< >` 없이 값만):
   ```
   CLOVA_OCR_INVOKE_URL=https://<id>.apigw.ntruss.com/custom/v1/.../general
   CLOVA_OCR_SECRET=<발급된 시크릿>
   ```
5. 백엔드 재시작 → 영수증 업로드 시 자동 인식(거래처·사업자번호·날짜·합계).

> `clovaocr-api-kr.ncloud.com/external/...` 형태는 내부(VPC)용이라 외부에서 호출되지 않습니다.
> 반드시 **APIGW 연동으로 나온 `apigw.ntruss.com` URL**을 사용하세요.

---

## 6. 테스트

```bash
pip install -r requirements-dev.txt
pytest                 # 55 케이스, 격리된 SQLite로 실행
```

각 테스트는 스키마 재생성·시드·업로드 저장소 초기화로 완전히 격리됩니다(`conftest.py`).

---

## 7. Docker 실행 (PostgreSQL)

```bash
docker compose up --build
```

- `db`(PostgreSQL 16) + `api`(FastAPI) 컨테이너 기동, `api`는 시작 시 `alembic upgrade head` 후 서버 실행.
- `.env`의 `DATABASE_URL`을 RDS로 바꾸면 운영 DB 연결.

---

## 8. 데이터베이스 마이그레이션 (운영)

```bash
alembic upgrade head                 # 초기 스키마 적용 (ea8d1e0dc89e)
# 모델 변경 후:
alembic revision --autogenerate -m "변경 내용"
alembic upgrade head
```

> `dev` 환경은 기동 시 테이블을 자동 생성하므로 로컬에서는 마이그레이션 없이도 동작합니다.

---

## 9. 역할별 사용 흐름

### 일반 직원
1. 로그인 → **경비 신청**
2. **📷 영수증 OCR** 로 사진 업로드(자동 인식) 또는 **+ 항목 추가**로 수동 입력
3. 계정과목·증빙유형 확인 → **신청서 저장** → 상세에서 **제출하기**

### 팀장
1. **승인함**에서 소속 팀 제출 건 확인 → **승인** 또는 **반려**(사유 입력)

### 경영지원실(관리자)
1. **승인함**에서 팀장승인 건 **검토완료**
2. **월 마감** → 귀속월 선택 → **마감 + 엑셀 생성** → **엑셀/증빙 ZIP 다운로드**
3. **관리** 화면에서 부서·팀·사용자 등록·수정

---

## 10. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 프론트에서 API 401 반복 | 토큰 만료 → 자동 재로그인. `.env`의 `JWT_SECRET`을 서버와 일치시켜 재시작 |
| CORS 오류 | 백엔드 `CORS_ORIGINS`에 프론트 주소(기본 `localhost:5173`) 포함 확인 |
| OCR이 항상 수동 폴백 | `.env`의 CLOVA 두 값이 채워졌는지, **apigw.ntruss.com** URL인지 확인 |
| OCR 연결 거부 | Invoke URL이 내부(VPC) 주소일 수 있음 → APIGW 자동 연동 URL 사용 |
| 증빙 이미지 404 | `UPLOAD_DIR` 경로/권한, 신청서 열람 권한 확인 |
| Windows 한글 인코딩 | `alembic.ini` 등 설정 파일은 ASCII 유지(프로젝트에 반영됨) |

---

## 11. 보안 주의 (공유·배포 시)

- `.env`, `storage/`, `*.db`는 **git에 포함되지 않습니다**(`.gitignore`).
- 실 자격증명이 채팅/문서/템플릿에 노출되었다면 **콘솔에서 즉시 재발급**하세요.
- 운영 배포 시 `JWT_SECRET`을 강력한 랜덤값으로 교체하고, 비밀은 Secrets Manager로 관리하세요.
