# Shadow_RolePlay_Agent API Spec

## 1. API 목록

| Method | Endpoint | 목적 |
|---|---|---|
| `POST` | `/shadow-roleplay/simulate` | 선택 팀에 대한 Shadow RolePlay 실행 |
| `GET` | `/shadow-roleplay/{simulation_id}` | simulation 결과 조회 |
| `GET` | `/shadow-roleplay/{simulation_id}/logs` | phase log 조회 |

## 2. `POST /shadow-roleplay/simulate`

Request:

```json
{
  "project_id": "project_001",
  "requirements_list_id": "req_001",
  "team_id": "team_001"
}
```

Response:

```json
{
  "simulation_id": "sim_001",
  "status": "completed",
  "simulation_output_uri": "gs://bucket/Simulation_OUTPUT.json"
}
```

## 3. `GET /shadow-roleplay/{simulation_id}`

Response:

```json
{
  "simulation_id": "sim_001",
  "team_id": "team_001",
  "status": "completed",
  "overall_project_fit": 73,
  "simulation_verdict": "proceed_with_conditions",
  "top_risks": [],
  "must_fix_before_start": []
}
```

## 4. `GET /shadow-roleplay/{simulation_id}/logs`

Response:

```json
{
  "simulation_id": "sim_001",
  "phase_logs": []
}
```

## 5. Error Response

```json
{
  "error_code": "SIMULATION_INPUT_MISSING",
  "message": "Selected_Team_Record is missing.",
  "details": []
}
```

Error Code:

| error_code | 의미 |
|---|---|
| `SIMULATION_INPUT_MISSING` | 필수 input 누락 |
| `PRIVACY_FILTER_FAILED` | 개인정보 제거 실패 |
| `AGENT_CARD_BUILD_FAILED` | Agent Card 생성 실패 |
| `ORCHESTRATION_FAILED` | simulation 진행 실패 |
| `ISSUE_EVALUATION_FAILED` | issue/risk 평가 실패 |
| `OUTPUT_VALIDATION_FAILED` | 최종 output schema validation 실패 |
