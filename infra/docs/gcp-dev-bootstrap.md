# GCP Dev Bootstrap

이 문서는 AI Org Simulation 프로젝트에서 수동으로 생성한 GCP 개발용 리소스를 기록한다.
아직 production 배포 구조를 확정한 것은 아니며, agent/backend 개발을 기다리는 동안 나중에
Cloud Run/Vertex AI/Storage 연동으로 넘어가기 쉽게 최소 리소스만 먼저 준비한 상태다.

## 현재 프로젝트

- Project ID: `ai-org-simulation-497121`
- Project number: `206678464190`
- 기본 region: `asia-northeast3`
- Storage location: `ASIA-NORTHEAST3`

## 활성화한 API

개발 프로젝트에서 아래 API를 활성화했다.

- `aiplatform.googleapis.com`
- `artifactregistry.googleapis.com`
- `cloudbuild.googleapis.com`
- `firestore.googleapis.com`
- `run.googleapis.com`
- `secretmanager.googleapis.com`
- `sqladmin.googleapis.com`
- `storage.googleapis.com`

`gcloud services list --enabled`를 실행하면 Google Cloud 기본 API들이 추가로 보일 수 있다.

## 생성한 리소스

### Cloud Storage

- Bucket: `gs://ai-org-sim-dev-artifacts-206678464190/`
- Location: `ASIA-NORTHEAST3`
- Storage class: `STANDARD`
- Public access prevention: `enforced`
- Uniform bucket-level access: `true`
- Soft delete retention: `7d`

개발 단계 용도:

- PRD 업로드 파일
- raw/derived dataset 백업
- simulation log
- generated report artifact

### Firestore

- Database: `(default)`
- Type: `FIRESTORE_NATIVE`
- Location: `asia-northeast3`
- Edition: `STANDARD`
- Free tier: enabled

개발 단계 용도:

- workflow status
- 가벼운 report snapshot
- dashboard에서 빠르게 조회할 상태 데이터

Firestore는 메인 관계형 DB가 아니다. HR, activity, feature, team, report 같은 구조화된
테이블은 배포 단계에서 Postgres/Cloud SQL을 기준으로 가져간다.

### Artifact Registry

- Repository: `ai-org-backend`
- Format: `DOCKER`
- Location: `asia-northeast3`
- Mode: `STANDARD_REPOSITORY`

개발 단계 용도:

- 나중에 Cloud Run으로 배포할 FastAPI backend Docker image 저장

### Service Account

- Name: `ai-org-backend-dev`
- Email: `ai-org-backend-dev@ai-org-simulation-497121.iam.gserviceaccount.com`
- 목적: 향후 Cloud Run backend runtime identity

Project-level IAM roles:

- `roles/aiplatform.user`
- `roles/datastore.user`
- `roles/secretmanager.secretAccessor`

Bucket-level IAM roles:

- `roles/storage.objectAdmin` on `gs://ai-org-sim-dev-artifacts-206678464190/`

### Secret Manager

생성한 secret:

- `backend-database-url`
- `vertex-location`
- `vertex-model`

현재 secret 값:

- `vertex-location`: `asia-northeast3`
- `vertex-model`: `gemini-2.5-flash`
- `backend-database-url`: placeholder만 생성함. Cloud SQL URL은 아직 없음.

Secret 값은 version 단위로 관리된다. 기존 값을 직접 수정하기보다 새 version을 추가한다.

## 확인 명령

```bash
gcloud config get-value project
gcloud services list --enabled
gcloud storage buckets list
gcloud firestore databases list
gcloud artifacts repositories list --location="asia-northeast3"
gcloud iam service-accounts list --filter="ai-org-backend-dev"
gcloud secrets list
```

backend service account의 project-level role 확인:

```bash
PROJECT_ID="ai-org-simulation-497121"
SA_EMAIL="ai-org-backend-dev@ai-org-simulation-497121.iam.gserviceaccount.com"

gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${SA_EMAIL}" \
  --format="table(bindings.role)"
```

bucket-level IAM 확인:

```bash
BUCKET="ai-org-sim-dev-artifacts-206678464190"

gcloud storage buckets get-iam-policy "gs://${BUCKET}"
```

## 아직 만들지 않은 것

아래 리소스는 배포 단계에 들어가기 전까지 만들지 않는다.

- Cloud SQL instance
- Cloud Run service deployment
- Firebase Hosting deployment
- GitHub Actions deployment workflow
- Workload Identity Federation
- Langfuse 또는 기타 observability stack

특히 Cloud SQL은 켜두면 지속 비용이 생긴다. 현재 Phase 4~5는 local Postgres와 dummy dataset,
derived JSON만으로 충분하므로 실제 배포 준비 단계에서 만든다.

## 나중에 배포할 때 이어서 할 일

Phase 7/8로 넘어가면 아래 순서로 진행한다.

1. `infra/` 아래에 Terraform 또는 다른 IaC 구조를 추가한다.
2. GitHub Actions 인증을 Workload Identity Federation으로 구성한다.
3. Cloud SQL을 생성하고 `backend-database-url` secret에 실제 연결 문자열 version을 추가한다.
4. backend Docker image를 빌드해서 Artifact Registry에 push한다.
5. `ai-org-backend-dev` service account로 FastAPI를 Cloud Run에 배포한다.
6. Firestore를 workflow/dashboard 상태 저장소로 계속 쓸지, MVP에서 제외할지 결정한다.
