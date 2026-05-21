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
├ backend/
│  ├ api/
│  ├ agents/
│  ├ orchestration/
│  ├ simulation/
│  ├ services/
│  ├ db/
│  └ core/
├ frontend/
├ packages/
│  └ prompts/
├ datasets/
├ infra/
├ scripts/
├ .env.example
├ docker-compose.yml
├ pnpm-workspace.yaml
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

## Getting Started

### 1) Clone

```bash
git clone <your-repo-url>
cd ai-org-simulation
```

### 2) Environment

```bash
cp .env.example .env
```

### 3) Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4) Frontend

```bash
cd frontend
pnpm install
pnpm dev
```
