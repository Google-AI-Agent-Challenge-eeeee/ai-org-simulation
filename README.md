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
