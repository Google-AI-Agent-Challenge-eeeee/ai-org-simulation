# Shadow_RolePlay_Agent Implementation Plan

## 1. 목적

`Shadow_RolePlay_Agent`는 팀 추천 이후 실행되는 프로젝트 진행 리스크 검증 Agent다.

이 Agent의 목적은 추천된 팀 조합이 실제 프로젝트를 진행한다고 가정했을 때, 정량 적합도 점수만으로는 발견하기 어려운 역할 충돌, 일정 병목, 연동 리스크, QA 누락, 업무 집중 리스크를 착수 전에 관찰하는 것이다.

핵심 포지셔닝:

```text
팀원 페르소나 기능이 아니라,
DB 기반 risk signal을 프로젝트 phase에서 검증하는 simulation layer
```

Shadow_RolePlay_Agent는 실제 결과물을 만들어내는 Agent가 아니다.  
이 Agent는 프로젝트 시작부터 종료까지의 진행 과정을 가상으로 관찰하고, 그 과정에서 발생할 수 있는 issue, risk, unresolved dependency, mitigation action을 구조화한다.

## 2. MVP 내 위치

```text
Requirements_List.json
→ 직원 DB와 compare
→ 직원 개인 적합도 순위 DB
→ Team 조합별 순위 DB
→ Shadow_RolePlay_Agent
→ Simulation_OUTPUT.json
→ 추천_OUTPUT.json 보정
→ Report_Files
```

Shadow Agent는 원천 Git/Jira/Slack/Calendar DB를 다시 직접 읽지 않는다.

앞단에서 이미 적합도 계산과 팀 조합 생성에 사용했기 때문에, Shadow Agent는 snapshot/summary/evidence 형태의 입력만 받는다.

이 구조의 장점:

- 같은 데이터를 반복 처리하지 않는다.
- 원문 Slack 메시지, 상세 Calendar 일정, 개인 프로필을 RolePlay 단계에 넣지 않는다.
- 직원 감시/개인 평가 서비스로 오해될 가능성을 줄인다.
- RolePlay는 원천 데이터가 아니라 앞단에서 계산된 risk signal을 프로젝트 phase에서 검증하는 계층이 된다.

## 3. Input

| Input | 설명 |
|---|---|
| `Requirements_List.json` | 프로젝트 기능, 역할, 기술, 일정, 제약, 리스크 |
| `Selected_Team_Record` | 선택된 팀 ID, 팀 순위, 팀 점수, 역할 배치 |
| `Employee_Fit_Profile_Snapshot` | 팀원별 역할, 스킬 매칭, capacity, delivery, communication signal |
| `Team_Risk_Summary` | 팀 단위 병목, 기술 gap, 일정, 협업 리스크 요약 |
| `Evidence_Metadata` | 각 risk signal이 어떤 원천 column에서 왔는지에 대한 참조 |

중요:

- `Git/Jira/Slack/Calendar DB` 원본은 직접 input이 아니다.
- 원문 Slack 메시지, 상세 Calendar 일정, 개인 프로필은 사용하지 않는다.
- 직원 이름은 그대로 사용한다. 이름 외 민감 정보(나이, 성별, 주소, 학교, 개인 프로필)는 제거한다.

## 4. Output

| Output | 설명 |
|---|---|
| `Team_Simulation_Log.json` | phase별 가상 프로젝트 진행 로그 |
| `Issue_Risk_Summary.json` | 발견된 issue, severity, evidence, root cause, mitigation |
| `Simulation_OUTPUT.json` | overall score, verdict, top risks, must-fix actions |

## 5. 세부 아키텍처

```text
Requirements_List.json
Selected_Team_Record
Employee_Fit_Profile_Snapshot
Team_Risk_Summary
Evidence_Metadata
→ Simulation_Input_Builder
→ Privacy_and_Column_Filter
→ Agent_Card_Builder
→ Scenario_Phase_Planner
→ Simulation_Orchestrator
→ A/B/C/D/E Role Agents
→ Phase_Log_Collector
→ Issue_Risk_Evaluator
→ Score_Calculator
→ Simulation Outputs
```

## 6. 모듈별 구현 계획

| 모듈 | 타입 | 핵심 기능 | 구현 근거 |
|---|---|---|---|
| `Simulation_Input_Builder` | Builder | 요구사항, 팀, 직원 snapshot을 하나의 packet으로 병합 | 발언과 리스크의 근거 추적 |
| `Privacy_and_Column_Filter` | Rule-based | 개인정보/원문 제거, 업무 signal만 유지 | 감시/사람평가 오해 방지 |
| `Agent_Card_Builder` | Builder | 팀원별 Agent Card 생성 | 역할 기반 시뮬레이션 단위 생성 |
| `Scenario_Phase_Planner` | Rule-based + LLM | phase별 agenda와 scenario event 생성 | 현업 SDLC 기반 흐름 구성 |
| `Simulation_Orchestrator` | LLM Agent | phase 진행, 발언 순서, 응답 형식 통제 | 자유 대화가 아닌 평가 가능한 로그 생성 |
| `Role Agents` | LLM Agents | 각 역할 관점에서 observation/concern/dependency/action 발화 | 역할 간 상호작용 관찰 |
| `Phase_Log_Collector` | Logger | 대화 요약, 발언, 이슈, 결정, action item 저장 | 분석 가능한 log 생성 |
| `Issue_Risk_Evaluator` | Rule-based + LLM | log와 risk signal 기반 issue 확정 | DB 가설과 simulation 관찰 결합 |
| `Score_Calculator` | Rule-based | 지표별 점수 및 overall fit 계산 | 팀별 비교 가능성 확보 |

## 7. 단계별 구현 상세

### Step 1. Simulation_Input_Builder

역할:

- `Requirements_List.json`, `Selected_Team_Record`, `Employee_Fit_Profile_Snapshot`, `Team_Risk_Summary`, `Evidence_Metadata`를 하나의 실행 packet으로 병합한다.
- 어떤 요구사항이 어떤 팀원과 연결되는지 정리한다.

Output:

```json
{
  "simulation_id": "sim_001",
  "project_context": {},
  "selected_team": {},
  "member_snapshots": [],
  "team_risk_summary": {},
  "evidence_metadata": []
}
```

구현 근거:

- Shadow RolePlay가 납득되려면 “왜 이 팀원이 이 발언을 하는가”가 추적 가능해야 한다.
- 입력을 packet으로 고정하면 팀별 simulation 비교가 가능하다.

### Step 2. Privacy_and_Column_Filter

역할:

- RolePlay에 필요한 업무적 신호만 남긴다.
- 개인정보, 원문 메시지, 개인 프로필은 제거한다.

유지 데이터:

- 역할
- 스킬 매칭
- missing skill
- capacity signal
- communication signal
- delivery signal
- risk tags
- evidence refs

제외 데이터:

- 이름, 나이, 성별, 주소
- Slack 원문 메시지
- Calendar 상세 일정 내용
- Jira/Slack 사용자 프로필 원문

구현 근거:

- 이 서비스는 사람 평가가 아니라 프로젝트 착수 전 팀 조합 검증 서비스다.
- 집계형 업무 신호만 사용해야 감시/차별 우려를 줄일 수 있다.

### Step 3. Agent_Card_Builder

역할:

- 팀원 5명이라면 각 직원의 이름을 그대로 사용해 Agent Card를 생성한다.
- 각 Agent는 이름을 가진 팀원 자체의 시뮬레이션이다. 역할·신호 데이터 범위 안에서 개인 성격과 감정 표현이 허용된다.

Agent Card 구조:

```json
{
  "agent_id": "홍길동",
  "assigned_role": "Backend Developer",
  "responsibilities": ["Payment API", "Database"],
  "strengths": ["Payment API 경험"],
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

주의사항:

- 역할·신호 데이터(skills, capacity, communication, delivery, collaboration)에서 파생된 범위 안에서 개인 성격과 감정 표현 가능.
- 동료를 이름으로 호칭한다 (예: "안우빈 씨", "권원솔 씨").
- 성별, 나이, 주소, 학교 등 PII는 넣지 않는다.
- 발언은 반드시 evidence 기반이어야 한다.

구현 근거:

- 페르소나를 억지로 넣는 것이 아니라, 팀 조합 점수만으로 보이지 않는 역할 간 상호작용을 관찰하기 위한 장치다.
- Agent Card는 DB 기반 evidence를 포함하므로 발언 근거를 설명할 수 있다.

### Step 4. Scenario_Phase_Planner

역할:

- 프로젝트 진행 단계를 생성한다.
- Requirements와 Team Risk Summary를 기반으로 phase별 agenda와 scenario event를 만든다.

고정 phase:

```text
Kickoff Meeting
→ Design Phase
→ Development Phase
→ Integration Phase
→ QA / Release Phase
```

| Phase | 확인 내용 | 근거 |
|---|---|---|
| Kickoff | 목표 이해, R&R, owner, 일정 인식 | 역할/책임 불명확성 조기 발견 |
| Design | API, DB, 외부 의존성, 기술 선택 | 기술 복잡성과 설계 공백 확인 |
| Development | 업무 분배, 구현 병목, 리뷰 흐름 | 일정/업무 집중 리스크 확인 |
| Integration | FE/BE/API/DB 연동, 스펙 불일치 | 실제 충돌이 많이 드러나는 구간 |
| QA / Release | 테스트 범위, 결함, release blocker | QA 누락과 릴리즈 리스크 확인 |

구현 근거:

- 현업 SDLC를 MVP에 맞게 압축한 구조다.
- 역할 문제는 Kickoff에서, 기술 의존성은 Design에서, 병목은 Development에서, 연동 문제는 Integration에서, QA 누락은 Release 직전에 잘 드러난다.
- phase를 고정해야 여러 팀 후보를 같은 기준으로 비교할 수 있다.

### Step 5. Simulation_Orchestrator

역할:

- phase 진행 순서를 통제한다.
- Role Agent의 발언 순서를 관리한다.
- 자유 대화가 아니라 구조화 응답을 강제한다.

각 Agent 발언 형식:

```json
{
  "observation": "",
  "concern": "",
  "dependency": "",
  "proposed_action": ""
}
```

| 필드 | 의미 | 후속 연결 |
|---|---|---|
| `observation` | 현재 phase에서 관찰한 사실 | log evidence |
| `concern` | 발생 가능한 위험 | issue 후보 |
| `dependency` | 다른 역할/기능/API와의 의존성 | 일정/연동 risk |
| `proposed_action` | 완화 조치 | mitigation 판단 |

구현 근거:

- 자유 대화는 분석이 어렵다.
- 이 구조는 모든 발언을 issue, risk, action item, score로 변환할 수 있게 만든다.

### Step 6. Role Agents

역할:

- 각 팀원 Agent는 자신의 `Agent_Card`에 근거해 말한다.
- 역할, 책임, 제약, risk tag 밖의 내용을 임의로 생성하지 않는다.

예시:

```text
홍길동: Backend Developer 관점
김민지: Frontend Developer 관점
이수진: QA Engineer 관점
박준호: PM 관점
최영우: DevOps Engineer 관점
```

구현 근거:

- 직원의 인격을 재현하는 것이 아니라, 프로젝트 역할 간 상호작용을 관찰하기 위한 구조다.
- 역할별 관점이 있어야 책임 충돌, 의존성, 연동 리스크, QA 누락이 드러난다.

### Step 7. Phase_Log_Collector

역할:

- 각 phase의 대화 요약, Agent 발언, issue, decision, action item을 저장한다.

Simulation Log 구조:

```json
{
  "simulation_id": "sim_001",
  "team_id": "team_001",
  "phase_logs": [
    {
      "phase_name": "Integration Phase",
      "scenario_event": "Payment API schema is not finalized",
      "trigger_source": [],
      "conversation_summary": "",
      "participant_turns": [],
      "detected_issues": [],
      "decisions": [],
      "action_items": [],
      "unresolved_questions": [],
      "phase_scores": {}
    }
  ]
}
```

Log 종류:

| Log | 설명 |
|---|---|
| `conversation_summary_log` | phase별 대화 요약 |
| `participant_turn_log` | Agent별 구조화 발언 |
| `trigger_source_log` | scenario event의 입력 근거 |
| `decision_log` | phase별 결정사항 |
| `action_item_log` | 담당자, 조치, 기한, 상태 |
| `issue_detection_log` | 감지된 issue와 severity |
| `unresolved_question_log` | 다음 phase로 넘어간 미해결 의존성 |
| `phase_score_log` | phase별 점수 |

구현 근거:

- 심사위원에게 중요한 것은 “AI가 말했다”가 아니라 “어떤 입력 근거 때문에 어떤 리스크가 관찰됐는가”다.
- `trigger_source`를 저장하면 결과 설명 가능성이 생긴다.

### Step 8. Issue_Risk_Evaluator

역할:

- simulation log와 pre-simulation risk signal을 함께 보고 issue를 확정한다.

Issue/Risk 평가 지표:

| 지표 | 의미 |
|---|---|
| `role_conflict` | 역할 또는 책임 충돌 |
| `unclear_ownership` | 기능/이슈 owner 공백 |
| `schedule_risk` | 일정 지연 가능성 |
| `workload_concentration` | 특정 팀원 업무 집중 |
| `technical_dependency_risk` | 기술/외부 API 의존성 |
| `integration_risk` | 연동 단계 충돌 가능성 |
| `communication_delay` | 응답/의사결정 지연 |
| `qa_coverage_gap` | 테스트 범위 누락 |
| `release_blocker` | 릴리즈 전 미해결 high issue |

최종 issue 판단:

```text
final_issue_score = 0.4 * pre_simulation_risk
                  + 0.6 * observed_simulation_risk
```

구현 근거:

- `pre_simulation_risk`는 과거 90일 업무 데이터 기반 가능성이다.
- `observed_simulation_risk`는 해당 프로젝트 맥락에서 실제로 관찰된 리스크다.
- 따라서 관찰 결과에 더 높은 비중을 둔다.

### Step 9. Score_Calculator

역할:

- issue/risk 결과를 기반으로 프로젝트 진행 안정성 점수를 계산한다.

최종 적합도:

```text
overall_project_fit =
schedule_stability * 0.20
+ role_clarity * 0.15
+ technical_risk_control * 0.15
+ integration_readiness * 0.15
+ collaboration_quality * 0.15
+ qa_release_readiness * 0.10
+ workload_balance * 0.10
```

가중치 근거:

- 일정 리스크는 프로젝트 실패 비용으로 가장 직접적으로 연결되므로 20%로 가장 높게 둔다.
- 역할, 기술, 연동, 협업은 프로젝트 진행 안정성의 핵심 축이므로 각각 15%로 둔다.
- QA/Release와 workload는 앞 지표와 일부 중복되므로 10% 보조 지표로 둔다.

## 8. Simulation 평가 Column 정책

Shadow Agent는 원천 업무 DB를 직접 읽지 않는다.  
다만 앞단에서 생성된 snapshot에는 아래와 같은 요약 signal이 포함되어야 한다.

| Snapshot Field | 설명 |
|---|---|
| `capacity_signal` | Calendar/Jira 기반 가용성 요약 |
| `communication_signal` | Slack/Jira 기반 응답/의사결정 지연 요약 |
| `delivery_signal` | Jira/Git 기반 업무 완료 안정성 요약 |
| `collaboration_signal` | Slack/Jira 기반 협업 접점 요약 |
| `risk_tags` | 팀원 또는 팀 단위 리스크 태그 |
| `evidence_refs` | 어떤 원천 column에서 signal이 왔는지 참조 |

원천 column을 직접 쓰지 않는 이유:

- 앞단 fit scoring에서 이미 사용했기 때문이다.
- Shadow Agent는 점수를 다시 계산하는 계층이 아니라 simulation 검증 계층이다.
- 개인정보 및 원문 데이터 노출을 최소화한다.

## 9. GCP 구현 위치

| GCP 서비스 | 사용 위치 |
|---|---|
| Cloud Run | Shadow RolePlay API 서버 |
| Vertex AI Gemini | Orchestrator, Role Agents, Issue summary |
| Firestore | Simulation Log, Issue Summary, Score 저장 |
| Cloud Storage | JSON output, Report Files 저장 |
| Cloud Logging | 실행 로그, 오류 기록 |

## 10. API 설계 초안

### `POST /shadow-roleplay/simulate`

Input:

```json
{
  "project_id": "project_001",
  "requirements_list_id": "req_001",
  "team_id": "team_001"
}
```

Output:

```json
{
  "simulation_id": "sim_001",
  "status": "completed",
  "simulation_output_uri": "gs://bucket/Simulation_OUTPUT.json"
}
```

## 11. 테스트 시나리오

| 테스트 | 기대 결과 |
|---|---|
| 결제 API 포함 프로젝트 | Integration risk와 QA failure-case gap 탐지 |
| 특정 Backend에게 업무 집중 | workload concentration 상승 |
| QA role이 약한 팀 | qa_coverage_gap 상승 |
| Slack/Jira 응답 지연 signal 높은 팀 | communication_delay 상승 |
| 모든 phase에서 unresolved high issue 없음 | `proceed` 또는 `proceed_with_conditions` |
| high issue가 QA/Release에 남음 | `needs_rebalancing` 또는 `not_recommended` |
| 개인정보가 포함된 snapshot 입력 | Privacy filter가 제거 |
| evidence가 없는 concern 생성 | Orchestrator가 재질문 또는 invalid 처리 |

## 12. Acceptance Criteria

- 원천 Git/Jira/Slack/Calendar DB를 직접 읽지 않는다.
- snapshot/summary/evidence 기반으로 Agent Card를 생성한다.
- 5개 phase가 순서대로 실행된다.
- Agent 발언은 구조화 형식으로 저장된다.
- issue는 evidence와 simulation log가 있을 때 확정된다.
- 최종 output은 추천 결과 보정까지 연결된다.
- 최종 점수는 사람 평가 점수가 아니라 프로젝트 조건에서의 팀 조합 안정성 점수로 표시된다.

## 13. MVP 구현 우선순위

1. Shadow RolePlay input schema 정의
2. Agent Card schema 정의
3. Simulation phase template 작성
4. Orchestrator prompt 작성
5. Role Agent prompt 작성
6. Phase Log schema 작성
7. Issue/Risk evaluator rule 작성
8. Score calculator 구현
9. Recommendation adjuster 구현
10. 샘플 팀 조합 기반 end-to-end simulation 테스트
