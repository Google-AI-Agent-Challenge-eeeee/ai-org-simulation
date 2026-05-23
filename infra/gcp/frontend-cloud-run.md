# Frontend Cloud Run Demo Deploy

이 문서는 Next.js frontend를 GCP Cloud Run에 수동 배포한 절차와 현재 상태를 기록한다.
현재 앱은 `/session/[id]`, `/report/[id]` 동적 라우트가 있으므로 Firebase Hosting 정적 배포보다
Cloud Run에서 Next 서버로 띄우는 방식이 더 안전하다.

## 현재 배포 상태

- Project: `ai-org-simulation-497121`
- Region: `asia-northeast3`
- Service: `ai-org-frontend`
- Service URL: `https://ai-org-frontend-ds2nbmznca-du.a.run.app`
- Backend API URL: `https://ai-org-backend-206678464190.asia-northeast3.run.app`
- Artifact Registry repository: `ai-org-frontend`
- Image: `asia-northeast3-docker.pkg.dev/ai-org-simulation-497121/ai-org-frontend/web:3e113bc`
- Runtime service account: `ai-org-frontend-dev`
- Public access: `--allow-unauthenticated`

## 2026-05-23 Smoke Result

검증한 URL:

```text
GET /
GET /simulate
```

결과:

```text
/         -> 200
/simulate -> 200
```

프론트 빌드 검증:

```bash
cd frontend
pnpm lint
pnpm build
```

## Build/Deploy Commands

repo root에서 실행한다.

```bash
export PROJECT_ID="ai-org-simulation-497121"
export REGION="asia-northeast3"
export BACKEND_URL="https://ai-org-backend-206678464190.asia-northeast3.run.app"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-org-frontend/web:latest"

gcloud config set project "${PROJECT_ID}"
gcloud auth configure-docker "${REGION}-docker.pkg.dev"

docker build \
  -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL="${BACKEND_URL}" \
  --build-arg NEXT_PUBLIC_MOCK=false \
  -t "${IMAGE}" \
  frontend

docker push "${IMAGE}"

gcloud run deploy ai-org-frontend \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --service-account="ai-org-frontend-dev@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars="NODE_ENV=production,NEXT_PUBLIC_MOCK=false,NEXT_PUBLIC_API_URL=${BACKEND_URL}" \
  --port=8080 \
  --allow-unauthenticated
```

배포 URL 확인:

```bash
gcloud run services describe ai-org-frontend \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)"
```

## Notes

- `NEXT_PUBLIC_*` 값은 클라이언트 번들에 들어가므로 Docker build 시점에도 반드시 전달해야 한다.
- frontend Cloud Run은 GCP 리소스를 직접 읽지 않으므로 backend service account를 재사용하지 않는다.
- Firebase Hosting은 나중에 커스텀 도메인/프록시가 필요할 때 Cloud Run 앞단으로 붙이는 선택지가 더 적합하다.
