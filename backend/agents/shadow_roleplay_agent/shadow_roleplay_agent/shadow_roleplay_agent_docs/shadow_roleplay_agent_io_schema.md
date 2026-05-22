# Shadow_RolePlay_Agent I/O Schema

## 1. 목적

이 문서는 Shadow_RolePlay_Agent의 input, intermediate output, final output 구조를 정의한다.

Shadow_RolePlay_Agent는 원천 Git/Jira/Slack/Calendar DB를 직접 읽지 않고, 앞단에서 생성된 snapshot, summary, evidence만 입력으로 받는다.

## 2. Final Input

| Input | 설명 | 사용 위치 |
|---|---|---|
| `Requirements_List.json` | 프로젝트 기능, 역할, 기술, 일정, 제약, 리스크 | project context, phase planning |
| `Selected_Team_Record` | 선택된 팀 ID, 팀 순위, 팀 점수, 역할 배치 | simulation 대상 팀 정의 |
| `Employee_Fit_Profile_Snapshot` | 팀원별 역할, 스킬 매칭, capacity, delivery, communication signal | Agent Card 생성 |
| `Team_Risk_Summary` | 팀 단위 병목, 기술 gap, 일정, 협업 리스크 요약 | scenario event, issue prior |
| `Evidence_Metadata` | risk signal이 어떤 원천 column에서 왔는지 참조 | trigger_source, 설명 가능성 |

## 3. Input 예시

### 3.1 `Selected_Team_Record`

```json
{
  "team_id": "team_001",
  "team_rank": 1,
  "team_fit_score": 87,
  "member_ids": ["emp_a", "emp_b", "emp_c", "emp_d", "emp_e"],
  "assigned_roles": {
    "emp_a": "Backend Developer",
    "emp_b": "Frontend Developer",
    "emp_c": "QA Engineer",
    "emp_d": "PM",
    "emp_e": "DevOps Engineer"
  },
  "role_coverage_score": 0.92,
  "skill_coverage_score": 0.88,
  "availability_score": 0.74,
  "team_risk_flags": ["backend_workload_concentration", "external_api_dependency"]
}
```

### 3.2 `Employee_Fit_Profile_Snapshot`

```json
{
  "employee_name": "홍길동",
  "assigned_role": "Backend Developer",
  "matched_skills": ["Payment API", "Database"],
  "missing_skills": ["Cloud Run deployment"],
  "capacity_signal": "medium_risk",
  "communication_signal": "low_delay",
  "delivery_signal": "stable",
  "collaboration_signal": "backend_centered",
  "risk_tags": ["external_api_dependency"],
  "evidence_refs": ["jira.overdue_issue_count", "calendar.busy_minutes"]
}
```

### 3.3 `Team_Risk_Summary`

```json
{
  "team_id": "team_001",
  "risk_tags": [
    "backend_workload_concentration",
    "payment_api_integration_risk",
    "qa_coverage_gap"
  ],
  "risk_prior_scores": {
    "schedule_risk": 0.42,
    "integration_risk": 0.63,
    "qa_coverage_gap": 0.58
  }
}
```

## 4. Intermediate Output

| Output | 생성 주체 | 설명 |
|---|---|---|
| `Simulation_Input_Packet.json` | Simulation_Input_Builder | simulation 실행에 필요한 입력 묶음 |
| `Sanitized_Profile_Snapshot.json` | Privacy_and_Column_Filter | 개인정보 제거 후 업무 signal만 남긴 snapshot |
| `Agent_Cards.json` | Agent_Card_Builder | A/B/C/D/E Agent Card |
| `Simulation_Phase_Plan.json` | Scenario_Phase_Planner | phase 순서, agenda, scenario event |
| `Phase_Log.json` | Phase_Log_Collector | phase별 구조화 로그 |
| `Issue_Candidates.json` | Issue_Risk_Evaluator | issue 후보 |
| `Score_Breakdown.json` | Score_Calculator | 지표별 점수 |

## 5. Agent Card Schema

```json
{
  "agent_id": "홍길동",
  "assigned_role": "Backend Developer",
  "responsibilities": ["Payment API", "Database"],
  "strengths": ["Payment API experience"],
  "constraints": ["capacity_signal: medium_risk"],
  "risk_tags": ["external_api_dependency"],
  "collaboration_signal": "low_delay",
  "delivery_signal": "stable",
  "evidence_refs": ["jira.overdue_issue_count", "calendar.busy_minutes"],
  "speaking_rules": [
    "Speak only from assigned role",
    "Do not invent private facts",
    "Raise concerns only with evidence",
    "Return observation, concern, dependency, proposed_action"
  ]
}
```

## 6. Phase Log Schema

```json
{
  "phase_name": "Integration Phase",
  "scenario_event": "Payment API schema is not finalized",
  "trigger_source": [],
  "conversation_summary": "",
  "participant_turns": [
    {
      "agent_id": "홍길동",
      "role": "Backend Developer",
      "observation": "",
      "concern": "",
      "dependency": "",
      "proposed_action": ""
    }
  ],
  "detected_issues": [],
  "decisions": [],
  "action_items": [],
  "unresolved_questions": [],
  "phase_scores": {}
}
```

## 7. Final Output

| Output | 설명 |
|---|---|
| `Team_Simulation_Log.json` | phase별 가상 프로젝트 진행 로그 |
| `Issue_Risk_Summary.json` | 발견된 issue, severity, evidence, root cause, mitigation |
| `Simulation_OUTPUT.json` | overall score, verdict, top risks, must-fix actions |

## 8. Output 관리 기준

```text
project_id / team_id / simulation_id 기준으로 저장
중간 산출물 보존
개인정보 및 원천 업무 데이터 제외
raw_dialogue는 선택 저장
structured log를 기본 저장 형태로 사용
```
