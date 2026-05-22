# Shadow_RolePlay_Agent Phase Commands

## Phase 0. Input Contract & Sample 준비

### 1. Phase별 작업 지시 요청 멘트

```text
Shadow_RolePlay_Agent 구현을 시작하기 위해 필요한 input schema와 sample 데이터를 준비해줘.
Requirements_List.json, Selected_Team_Record, Employee_Fit_Profile_Snapshot, Team_Risk_Summary, Evidence_Metadata의 필수 필드와 예시를 정의해줘.
```

### 2. Phase별 필수 필요 파일

```text
Final_shdow_roleplay_agent_implementation_plan.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
requirements_agent/requirements_agent_docs/requirements_agent_io_schema.md
```

## Phase 1. Simulation Input Builder

### 1. Phase별 작업 지시 요청 멘트

```text
Requirements_List.json, Selected_Team_Record, Employee_Fit_Profile_Snapshot, Team_Risk_Summary, Evidence_Metadata를 하나의 Simulation_Input_Packet.json으로 병합하는 Simulation_Input_Builder를 구현해줘.
각 risk와 agent 발언이 어떤 evidence에서 왔는지 추적 가능해야 해.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
```

## Phase 2. Privacy & Column Filter

### 1. Phase별 작업 지시 요청 멘트

```text
Shadow RolePlay 입력에서 직원 실명, 원문 Slack 메시지, 상세 Calendar 일정, 개인 프로필을 제거하고,
역할, 스킬, capacity, delivery, communication, risk_tags, evidence_refs만 남기는 Privacy_and_Column_Filter를 구현해줘.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
```

## Phase 3. Agent Card Builder

### 1. Phase별 작업 지시 요청 멘트

```text
팀원별 Employee_Fit_Profile_Snapshot을 기반으로 직원 이름을 그대로 사용하는 Agent Card를 생성하는 Agent_Card_Builder를 구현해줘.
Agent Card에는 assigned_role, responsibilities, strengths, constraints, risk_tags, evidence_refs, speaking_rules가 포함되어야 해.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
```

## Phase 4. Scenario Phase Planner

### 1. Phase별 작업 지시 요청 멘트

```text
Requirements_List와 Team_Risk_Summary를 기반으로 Kickoff, Design, Development, Integration, QA/Release 5개 phase의 agenda와 scenario_event를 생성하는 Scenario_Phase_Planner를 구현해줘.
각 scenario_event에는 trigger_source가 포함되어야 해.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_rules.md
Token_limit_Verify_phase.md
```

## Phase 5. Simulation Orchestrator

### 1. Phase별 작업 지시 요청 멘트

```text
각 phase의 진행 순서, Role Agent 발언 순서, 응답 형식, 재질문 규칙을 통제하는 Simulation_Orchestrator를 구현해줘.
Agent 발언은 observation, concern, dependency, proposed_action 형식으로만 저장되도록 강제해줘.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
```

## Phase 6. Role Agent Execution

### 1. Phase별 작업 지시 요청 멘트

```text
각 Role Agent가 자신의 Agent Card와 현재 phase context에 근거해 발언하도록 Role Agent 실행 로직을 구현해줘.
Agent는 주어진 evidence 밖의 개인정보나 사실을 생성하면 안 되고, 역할 관점에서 observation, concern, dependency, proposed_action만 반환해야 해.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
Agent_Cards.json
Simulation_Phase_Plan.json
```

## Phase 7. Phase Log Collector

### 1. Phase별 작업 지시 요청 멘트

```text
phase별 conversation_summary, participant_turns, trigger_source, detected_issues, decisions, action_items, unresolved_questions, phase_scores를 저장하는 Phase_Log_Collector를 구현해줘.
raw_dialogue는 선택 저장으로 두고, 기본은 구조화 로그 중심으로 저장해줘.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
```

## Phase 8. Issue/Risk Evaluator

### 1. Phase별 작업 지시 요청 멘트

```text
structured phase log와 Team_Risk_Summary를 기반으로 role_conflict, schedule_risk, integration_risk, qa_coverage_gap 등 issue/risk를 확정하는 Issue_Risk_Evaluator를 구현해줘.
issue는 evidence와 simulation log 근거가 있을 때만 확정해줘.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_rules.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
Team_Simulation_Log.json
Team_Risk_Summary.json
```

## Phase 9. Score Calculator

### 1. Phase별 작업 지시 요청 멘트

```text
Issue_Risk_Summary를 기반으로 schedule_stability, role_clarity, technical_risk_control, integration_readiness, collaboration_quality, qa_release_readiness, workload_balance 점수를 계산하는 Score_Calculator를 구현해줘.
최종 overall_project_fit은 정의된 가중치 공식을 따라 계산해줘.
```

### 2. Phase별 필수 필요 파일

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_rules.md
Issue_Risk_Summary.json
```

