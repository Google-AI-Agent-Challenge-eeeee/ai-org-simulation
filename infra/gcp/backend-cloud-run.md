# Backend Cloud Run Demo Deploy

이 문서는 FastAPI backend를 GCP 데모 환경에 수동 배포하는 절차다.
운영 자동 배포가 아니라, 로컬 MVP 플로우를 Cloud Run에서 한 번 검증하는 것이 목표다.

## 대상 구조

```text
Cloud Run backend
→ Cloud SQL Postgres
→ Secret Manager
→ Artifact Registry
→ Vertex AI는 우선 stub mode 유지
```

## 전제

- GCP project: `ai-org-simulation-497121`
- Region: `asia-northeast3`
- Artifact Registry repository: `ai-org-backend`
- Runtime service account: `ai-org-backend-dev`
- Secret Manager secrets:
  - `backend-database-url`
  - `vertex-location`
  - `vertex-model`

Cloud SQL은 비용이 발생한다. 데모 이후 필요 없으면 instance를 중지하거나 삭제한다.

## 2026-05-23 smoke 결과

이번 smoke는 비용과 복잡도를 줄이기 위해 Cloud SQL을 붙이지 않고 실행했다.
팀 랭킹은 컨테이너 이미지에 포함된 `datasets/raw` CSV를 읽고, LLM은 `stub` 모드를 사용한다.

- Project: `ai-org-simulation-497121`
- Region: `asia-northeast3`
- Service: `ai-org-backend`
- Service URL: `https://ai-org-backend-206678464190.asia-northeast3.run.app`
- Image: `asia-northeast3-docker.pkg.dev/ai-org-simulation-497121/ai-org-backend/api:b81b5a4`
- Source branch: `service/refactor/team-ranking-adapter`
- Source commit: `b81b5a4`
- Cloud SQL: 미연결
- Public access: `--allow-unauthenticated`

검증한 endpoint:

```text
GET  /health
POST /api/sessions
GET  /api/sessions/{id}/requirements
GET  /api/sessions/{id}/teams
GET  /api/sessions/{id}/stream?mode=stub
```

확인한 동작:

- `/health`가 `status=ok`, `env=staging`, `llm_mode=stub`을 반환한다.
- session 생성, requirements 분석, Top 1 team 생성이 동작한다.
- 최초 입력한 `pmPersona.name`이 팀 PM과 RolePlay packet에 유지된다.
- SSE stream이 `status`, `backend_log` 이벤트를 반환한다.

Cloud SQL 없이 재배포할 때는 아래 명령을 사용한다.

```bash
export PROJECT_ID="ai-org-simulation-497121"
export REGION="asia-northeast3"
export SERVICE_NAME="ai-org-backend"
export AR_REPO="ai-org-backend"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/api:b81b5a4"
export SA_EMAIL="ai-org-backend-dev@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "${PROJECT_ID}"
gcloud auth configure-docker "${REGION}-docker.pkg.dev"

docker build -f backend/Dockerfile -t "${IMAGE}" .
docker push "${IMAGE}"

gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=1 \
  --set-env-vars="ENV=staging,LOG_LEVEL=INFO,LLM_MODE=stub,GCP_PROJECT_ID=${PROJECT_ID},CORS_ALLOW_ORIGINS=[*]" \
  --port=8080 \
  --allow-unauthenticated
```

로컬 프론트에서 이 Cloud Run backend를 보려면 `frontend/.env.local`을 아래처럼 둔다.
이 파일은 개인 로컬 설정이며 Git에 올리지 않는다.

```env
NEXT_PUBLIC_MOCK=false
NEXT_PUBLIC_API_URL=https://ai-org-backend-206678464190.asia-northeast3.run.app
```

## 1. Cloud Shell 변수

```bash
export PROJECT_ID="ai-org-simulation-497121"
export PROJECT_NUMBER="206678464190"
export REGION="asia-northeast3"
export SERVICE_NAME="ai-org-backend"
export AR_REPO="ai-org-backend"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/api:latest"
export SQL_INSTANCE="ai-org-postgres-dev"
export DB_NAME="ai_org_simulation"
export DB_USER="ai_org_app"
export SA_EMAIL="ai-org-backend-dev@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "${PROJECT_ID}"
```

## 2. Cloud SQL 생성

이미 instance가 있으면 이 단계는 건너뛴다.

```bash
read -s DB_PASSWORD

gcloud sql instances create "${SQL_INSTANCE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --database-version=POSTGRES_16 \
  --cpu=1 \
  --memory=3840MiB \
  --storage-size=10GB \
  --storage-type=SSD \
  --availability-type=ZONAL \
  --root-password="${DB_PASSWORD}"

gcloud sql databases create "${DB_NAME}" \
  --instance="${SQL_INSTANCE}"

gcloud sql users create "${DB_USER}" \
  --instance="${SQL_INSTANCE}" \
  --password="${DB_PASSWORD}"
```

## 3. DATABASE_URL secret 갱신

Cloud Run에서 Cloud SQL Unix socket으로 접속하는 URL을 secret에 저장한다.

```bash
export INSTANCE_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
export DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${INSTANCE_CONNECTION_NAME}"

printf "%s" "${DATABASE_URL}" | gcloud secrets versions add backend-database-url \
  --data-file=-
```

## 4. DB migration/seed

Cloud SQL Auth Proxy로 Cloud SQL에 붙어서 migration과 seed를 실행한다.
아래 명령은 repo가 Cloud Shell에 clone되어 있고 `uv`가 설치되어 있다는 가정이다.

```bash
curl -L -o cloud-sql-proxy \
  https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.18.3/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

./cloud-sql-proxy "${INSTANCE_CONNECTION_NAME}" --port 5433 &
export DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5433/${DB_NAME}"

uv run alembic upgrade head
uv run python scripts/dev/seed_all.py
```

## 5. Docker image build/push

repo root에서 실행한다.

```bash
gcloud auth configure-docker "${REGION}-docker.pkg.dev"

docker build \
  -f backend/Dockerfile \
  -t "${IMAGE}" \
  .

docker push "${IMAGE}"
```

## 6. Cloud Run deploy

```bash
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --add-cloudsql-instances="${INSTANCE_CONNECTION_NAME}" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=1 \
  --set-env-vars="ENV=staging,LOG_LEVEL=INFO,LLM_MODE=stub,GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-secrets="DATABASE_URL=backend-database-url:latest,VERTEX_LOCATION=vertex-location:latest,VERTEX_MODEL=vertex-model:latest" \
  --allow-unauthenticated
```

배포 URL 확인:

```bash
gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --format="value(status.url)"
```

## 7. Smoke test

```bash
export BACKEND_URL="$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')"

curl "${BACKEND_URL}/health"
curl -X POST "${BACKEND_URL}/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{"prd":"# Demo\n\nGoal: Build a demo service."}'
```

## 8. Frontend 연결

로컬 프론트에서 Cloud Run backend를 보려면 `frontend/.env.local`을 바꾼다.

```env
NEXT_PUBLIC_MOCK=false
NEXT_PUBLIC_API_URL=https://YOUR_CLOUD_RUN_URL
```

그 다음:

```bash
cd frontend
pnpm dev
```

## 참고

- 이 단계에서는 `LLM_MODE=stub`을 유지한다.
- Vertex 전환은 Cloud Run 배포가 안정화된 뒤 별도 브랜치에서 진행한다.
- 자동 배포 GitHub Actions는 수동 배포가 한 번 성공한 뒤 추가한다.
