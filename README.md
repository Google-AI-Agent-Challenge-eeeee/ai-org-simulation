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

# Python 가상환경 + 의존성 자동 설치
just setup                  # 내부적으로 'uv sync' 실행

# 로컬 Postgres 컨테이너 기동
just db-up
```

`just setup`은 루트에 `.venv/`를 만들고 `pyproject.toml`에 정의된 모든 Python 의존성을 설치합니다.

### Step 4. IDE 설정

처음 VSCode/Cursor에서 프로젝트를 열면 우측 하단에 추천 확장 설치 팝업이 뜹니다. **"Install All"** 클릭만 하면 끝입니다. 추천 확장 목록은 [.vscode/extensions.json](.vscode/extensions.json) 참조.

Python 인터프리터는 `.venv/`를 자동 인식합니다. 인식되지 않으면 `Ctrl+Shift+P` → `Python: Select Interpreter` → `.venv` 선택.

### Step 5. 매일 쓰는 명령

```bash
just                # 사용 가능한 명령 목록
just dev            # FastAPI dev 서버 (auto-reload)
just db-up          # Postgres 컨테이너 시작
just db-down        # 모든 docker-compose 서비스 정지
just lint           # ruff 검사 (코드 변경 없음)
just fmt            # ruff 자동 포맷 + auto-fix
just test           # pytest 실행
```

> 모든 명령은 `uv run`을 통해 가상환경에서 실행되므로, 별도로 venv를 activate할 필요가 없습니다.

### Step 6. 동작 검증

`just dev` 실행 후 브라우저에서 다음 두 URL을 열어 확인:

- `http://localhost:8000/health` → `{"status":"ok"}`
- `http://localhost:8000/docs` → Swagger UI

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
