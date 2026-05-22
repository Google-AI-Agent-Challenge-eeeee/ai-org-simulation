# AI Org Simulation

AI 기반 가상 조직 시뮬레이션 프로젝트입니다.  
PRD와 PM 스타일을 입력받아 요구사항을 분석하고, 직원/협업 데이터를 바탕으로 팀 조합을 평가한 뒤, 페르소나 시뮬레이션 결과와 정량 평가를 합쳐 최종 리포트를 생성합니다.

## Current Scope (MVP)

- 외부 API(`GitHub`, `Slack`, `Jira`, `Google Calendar`) 자동 수집은 **현재 미구현**
- 대신 `datasets/`에 더미 데이터를 넣어 엔진을 개발/검증
- 이후 API 수집 레이어를 붙여도 상위 파이프라인이 유지되도록 구조화

## Repository Structure

```text
ai-org-simulation/
├ backend/                 # FastAPI 백엔드
│  ├ api/                  # 라우터
│  ├ agents/               # AI 에이전트
│  ├ orchestration/        # 워크플로우
│  ├ simulation/           # 섀도우 롤플레이 엔진
│  ├ services/             # 외부 서비스 연동 (Vertex AI 등)
│  ├ db/                   # ORM/repository
│  └ core/                 # 설정, 상수, 로거
├ frontend/                # Next.js 대시보드 (예정)
├ packages/
│  └ prompts/              # 공용 프롬프트 자산
├ datasets/                # 더미 데이터 / 파생 데이터
├ infra/                   # GCP / Docker / CI
├ scripts/                 # seed / fake-data / dev 스크립트
├ pyproject.toml           # Python 의존성 + ruff 설정 (uv 관리)
├ uv.lock                  # Python 잠금 파일 (uv 자동 생성)
├ justfile                 # 공용 개발 명령
├ docker-compose.yml       # 로컬 Postgres
├ pnpm-workspace.yaml
├ .gitattributes / .editorconfig / .vscode/
├ .env.example
└ .gitignore
```

## Convention

이 프로젝트는 `frontend`, `backend`, `agents`, `simulation`, `datasets`, `infra` 등 여러 개발 영역이 함께 존재하므로 커밋 메시지와 브랜치 이름의 prefix를 통일합니다.

### Commit Message

```text
<scope>/<type>: <summary>
```

예시:

```text
api/feat: 요구사항 분석 API 개발
api/fix: 요청 검증 로직 수정
agent/feat: 페르소나 생성 에이전트 추가
agent/fix: 시뮬레이션 응답 파싱 오류 수정
simulation/feat: 회의 턴 매니저 개발
data/chore: 더미 HR 데이터 추가
infra/feat: Docker 실행 환경 추가
docs/update: README 컨벤션 문서화
```

### Scope

- `front`: 프론트엔드 화면, 컴포넌트, 상태 관리
- `api`: FastAPI 라우터, 요청/응답 처리
- `agent`: AI 에이전트 구현
- `orchestration`: 워크플로우 연결 및 실행 순서
- `simulation`: 섀도우 롤플레이 시뮬레이션 엔진
- `service`: 외부 서비스 연동 계층
- `db`: 데이터베이스, repository, query
- `core`: 설정, 상수, 보안, 로거
- `prompt`: 프롬프트 자산
- `data`: 더미 데이터, fixture, seed 데이터
- `infra`: Docker, GCP, Firebase, 배포 환경
- `script`: 개발/평가/시드 스크립트
- `docs`: 문서
- `chore`: 기타 설정, 정리 작업

### Type

- `feat`: 새로운 기능 개발
- `fix`: 버그 수정
- `update`: 기존 기능 개선
- `refactor`: 동작 변경 없는 구조 개선
- `test`: 테스트 추가/수정
- `docs`: 문서 작업
- `chore`: 설정, 패키지, 빌드 등 기타 작업

### Branch Naming

브랜치도 커밋과 같은 prefix 체계를 사용합니다.

```text
<scope>/<type>/<short-description>
```

예시:

```bash
git checkout -b api/feat/requirement-analysis
git checkout -b agent/fix/persona-response-parser
git checkout -b simulation/feat/meeting-turn-manager
git checkout -b data/chore/dummy-employee-dataset
git checkout -b infra/feat/docker-compose
git checkout -b docs/update/readme-convention
```

## Team Onboarding

처음 클론한 팀원은 아래 순서대로만 진행하면 됩니다. 맥/윈도우 사용자가 섞여 있어도 모두 같은 `just` 명령으로 동작합니다.

### Step 1. 필수 도구 설치 (머신당 1회)

우리가 이 도구들을 쓰는 이유:

- `Git`: 코드 버전 관리와 브랜치/PR 협업을 위한 기본 도구입니다.
- `Docker Desktop`: 로컬 Postgres처럼 팀원이 동일한 인프라 환경을 띄우기 위해 사용합니다.
- `uv`: Python 가상환경, 의존성 설치, 잠금 파일(`uv.lock`) 관리를 빠르고 동일하게 처리합니다.
- `just`: 맥/윈도우 명령어 차이를 숨기고 `just dev`, `just lint`처럼 공통 명령으로 개발하게 해줍니다.
- `Node.js` + `corepack`: 프론트엔드 작업자가 `pnpm`을 동일한 방식으로 사용할 수 있게 합니다.

#### Windows (PowerShell)

```powershell
winget install Git.Git
winget install Docker.DockerDesktop
winget install astral-sh.uv
winget install Casey.Just
# (프론트엔드 작업자만)
winget install OpenJS.NodeJS.LTS
corepack enable
```

#### macOS

```bash
brew install git
brew install --cask docker
brew install uv
brew install just
# (프론트엔드 작업자만)
brew install node
corepack enable
```

> Docker Desktop은 설치 후 한 번 실행해서 라이선스에 동의해야 컨테이너가 뜹니다.

### Step 2. Git 줄바꿈 설정 (머신당 1회)

레포의 `.gitattributes`가 LF를 강제하지만, 안전하게 글로벌 설정도 한 번 맞춰주세요.

#### Windows

```powershell
git config --global core.autocrlf false
git config --global core.eol lf
```

#### macOS

```bash
git config --global core.autocrlf input
git config --global core.eol lf
```

### Step 3. 레포 클론 후 셋업 (클론마다 1회)

```bash
git clone <your-repo-url>
cd ai-org-simulation

# 환경 변수 파일 준비
cp .env.example .env        # PowerShell: copy .env.example .env

# 한 방에 끝내기: 의존성 설치 → Postgres 기동 → 마이그레이션 적용
just bootstrap
```

`just bootstrap`은 다음 순서로 자동 실행됩니다:

1. `uv sync` — 루트에 `.venv/`를 만들고 `pyproject.toml`의 모든 Python 의존성 설치
2. `docker compose up -d postgres` — 로컬 Postgres 컨테이너 기동
3. `wait_for_postgres.py` — DB가 연결 가능한 상태가 될 때까지 대기
4. `alembic upgrade head` — 최신 스키마 마이그레이션 적용

개별 단계로 실행하고 싶다면 `just setup` → `just db-up` → `just db-migrate`.

### Step 4. IDE 설정

처음 VSCode/Cursor에서 프로젝트를 열면 우측 하단에 추천 확장 설치 팝업이 뜹니다. **"Install All"** 클릭만 하면 끝입니다. 추천 확장 목록은 [.vscode/extensions.json](.vscode/extensions.json) 참조.

Python 인터프리터는 `.venv/`를 자동 인식합니다. 인식되지 않으면 `Ctrl+Shift+P` → `Python: Select Interpreter` → `.venv` 선택.

### Step 5. 매일 쓰는 명령

```bash
just                          # 사용 가능한 명령 목록
just dev                      # FastAPI dev 서버 (auto-reload)
just db-up                    # Postgres 컨테이너 시작
just db-down                  # 모든 docker-compose 서비스 정지
just db-migrate               # 미적용 Alembic 마이그레이션 실행 (upgrade head)
just db-revision "메시지"     # 모델 변경분으로 새 마이그레이션 자동 생성
just db-reset                 # 로컬 DB 완전 삭제 후 재생성 (DESTRUCTIVE)
just seed                     # datasets/raw/*.csv → DB 적재 (TRUNCATE 후 재삽입, 멱등)
just lint                     # ruff 검사 (코드 변경 없음)
just fmt                      # ruff 자동 포맷 + auto-fix
just test                     # pytest unit only (DB 불필요, 빠름)
just test-integration         # API 통합 테스트 (just db-up && just seed 선행 필요)
just test-all                 # unit + integration 전부
```

#### DB 스키마를 바꿨다면

1. `backend/db/models/*.py`에서 SQLAlchemy 모델 수정
2. `just db-revision "describe the change"` 실행 → 새 마이그레이션 파일 생성
3. 생성된 파일을 한 번 훑어보고 (autogenerate가 놓치는 경우 있음) 커밋
4. 팀원은 풀(pull) 후 `just db-migrate` 한 줄로 동기화

#### 더미 데이터 로딩

`just seed` 한 줄이면 `datasets/raw/{hr,github,slack,jira,calendar}/*.csv`가 전부 DB에 들어갑니다.
실행 전 각 테이블을 `TRUNCATE ... RESTART IDENTITY CASCADE`로 비우므로 몇 번을 돌려도 결과는 동일합니다(전 도메인 100행씩 = 500행).
CSV → Pydantic 검증 → ORM insert 순서라 스키마 drift가 있으면 시드 단계에서 바로 잡힙니다.

> 모든 명령은 `uv run`을 통해 가상환경에서 실행되므로, 별도로 venv를 activate할 필요가 없습니다.

### Step 6. 동작 검증

`just dev` 실행 후 브라우저에서 다음 두 URL을 열어 확인:

- `http://localhost:8000/health` → `{"status":"ok"}`
- `http://localhost:8000/docs` → Swagger UI (모든 엔드포인트를 클릭만으로 호출 가능)

#### 현재 노출된 API (Phase 3 — read-only)

모두 GET. 응답은 Pydantic 스키마와 동일한 모양이고, list 계열은 `Paginated[T]`(`total/limit/offset/items`)로 감싸져 있습니다.

| Method & Path | 설명 | 주요 쿼리 파라미터 |
| --- | --- | --- |
| `GET /health` | 헬스 체크 | — |
| `GET /employees` | 직원 목록 (페이지네이션) | `limit`, `offset`, `department`, `job_category_code` |
| `GET /employees/{employee_id}` | 직원 1명 상세 | — |
| `GET /employees/{employee_id}/profile` | **HR + GitHub + Slack + Jira + Calendar 합본** | — |
| `GET /github/activities` | GitHub 활동 행 (한 사람당 여러 측정 기간) | `limit`, `offset`, `github_id` |
| `GET /slack/activities` | Slack 활동 행 (사람당 1행) | `limit`, `offset`, `slack_user_id` |
| `GET /jira/activities` | Jira 활동 행 (사람당 1행) | `limit`, `offset`, `jira_account_id` |
| `GET /calendar/activities` | Calendar 활동 행 (사람당 여러 캘린더 가능) | `limit`, `offset`, `google_email` |

빠른 확인 예시:

```bash
curl http://localhost:8000/employees?limit=3
curl http://localhost:8000/employees/E20260001/profile
curl "http://localhost:8000/github/activities?github_id=gh-emp-0001"
```

> 별도 클라이언트 없이 `/docs`에서 `Try it out` → `Execute`만으로 모든 응답을 확인할 수 있습니다.

#### 테스트 레이어링

| 명령 | 무엇 | 언제 |
| --- | --- | --- |
| `just test` | unit only (SQLite + Pydantic 검증) | 매 커밋 전 (Postgres 없어도 OK) |
| `just test-integration` | API 통합 — 실 Postgres + 시드된 데이터 | 라우터/DB 모델 변경 후, PR 올리기 전 |
| `just test-all` | unit + integration 모두 | 큰 PR 마무리 시 |

`@pytest.mark.integration`이 붙은 테스트만 통합 카테고리. CI는 PR 시점에 통합 테스트도 자동으로 돕니다.

### Step 7. 풀(pull) 후 의존성이 바뀌었을 때

```bash
just setup          # uv sync 재실행
```

`pyproject.toml`이나 `uv.lock`이 변경된 PR을 머지/풀했다면 위 명령으로 venv를 동기화합니다.

---

## Frontend (예정)

Next.js 대시보드는 추후 추가됩니다. 셋업되면 다음과 같이 실행 예정:

```bash
pnpm install
pnpm --filter frontend dev
```
