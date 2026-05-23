# Vertex Demo Mode

Prototype demos can enable Vertex AI for the two LLM-backed flows while keeping
fallbacks enabled:

- Requirements Agent: PRD to requirements extraction.
- Shadow RolePlay Agent: persona meeting turns during the simulation stream.

## Cloud Run Update

```bash
gcloud run services update ai-org-backend \
  --region="asia-northeast3" \
  --project="ai-org-simulation-497121" \
  --update-env-vars="LLM_MODE=stub,REQUIREMENTS_LLM_MODE=vertex,SIMULATION_LLM_MODE=vertex,REQUIREMENTS_STRICT_LLM=false,ROLEPLAY_STRICT_LLM=false,VERTEX_LOCATION=asia-northeast3,VERTEX_MODEL=gemini-2.5-flash"
```

## Mode Behavior

- `REQUIREMENTS_LLM_MODE=vertex`: Requirements Agent tries Vertex first.
- `SIMULATION_LLM_MODE=vertex`: Shadow RolePlay stream tries Vertex first.
- `*_STRICT_LLM=false`: failed Vertex calls fall back to deterministic stub output.
- `LLM_MODE=stub`: global default remains safe for flows without a per-flow override.

## Local Smoke

For local backend runs with Application Default Credentials:

```env
LLM_MODE=stub
REQUIREMENTS_LLM_MODE=vertex
SIMULATION_LLM_MODE=vertex
REQUIREMENTS_STRICT_LLM=false
ROLEPLAY_STRICT_LLM=false
GCP_PROJECT_ID=ai-org-simulation-497121
VERTEX_LOCATION=asia-northeast3
VERTEX_MODEL=gemini-2.5-flash
```
