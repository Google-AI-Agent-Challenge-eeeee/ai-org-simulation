# Final Shadow_RolePlay_Agent Implementation Plan

## 0. 문서 목적

이 문서는 ProjectFit AX MVP의 두 번째 핵심 Agent인 `Shadow_RolePlay_Agent` 구현을 위한 최종 implementation plan이다.

`Shadow_RolePlay_Agent`는 팀원 페르소나를 보여주기 위한 기능이 아니다. 이 Agent의 목적은 이미 생성된 `직원 개인 적합도 순위 DB`와 `Team 조합별 순위 DB`를 기반으로, 추천된 팀 조합이 실제 프로젝트를 진행한다고 가정했을 때 발생할 수 있는 역할 충돌, 일정 병목, 연동 리스크, QA 누락, 업무 집중 리스크를 착수 전에 검증하는 것이다.

핵심 역할:

```text
Requirements_List.json
+ Selected_Team_Record
+ Employee_Fit_Profile_Snapshot
+ Team_Risk_Summary
+ Evidence_Metadata
→ Shadow_RolePlay_Agent
→ Team_Simulation_Log.json
→ Issue_Risk_Summary.json
→ Simulation_OUTPUT.json
```

핵심 설계 원칙:

- 원천 Git/Jira/Slack/Calendar DB를 Shadow Agent가 직접 다시 읽지 않는다.
- 앞단에서 계산된 snapshot, summary, evidence만 사용한다.
- 직원 이름은 그대로 사용한다. 이름 외 민감 정보(나이, 성별, 주소, 학교, 개인 프로필)는 제거한다.
- Agent는 이름을 가진 팀원 자체의 시뮬레이션이다. 역할·신호 데이터 범위 안에서 개인 성격과 감정 표현이 허용된다.
- RolePlay는 자유 대화가 아니라 Orchestrator가 통제하는 structured simulation이다.
- 각 Agent 발언은 `observation`, `concern`, `dependency`, `proposed_action` 형식으로 제한한다.
- 최종 점수는 사람 평가 점수가 아니라 해당 프로젝트 조건에서의 팀 조합 안정성 점수다.

---

## 1. Shadow_RolePlay_Agent 세부 아키텍처

### 1.1 MVP 내 위치

```text
Requirements_List.json
→ 직원 DB와 compare
→ 직원 개인 적합도 순위 DB
→ Team 조합별 순위 DB
→ Shadow_RolePlay_Agent
→ Simulation_OUTPUT.json
→ Report_Files
```

Shadow_RolePlay_Agent는 팀 추천 이후 실행되는 검증 계층이다.  
앞단의 정량 점수는 "이 팀이 요구사항에 얼마나 잘 맞는가"를 계산하고, Shadow RolePlay는 "이 팀이 실제로 프로젝트를 진행하면 어디서 문제가 생기는가"를 관찰한다.

### 1.2 세부 데이터 흐름

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

### 1.3 구성 요소 요약

| 구성 요소 | 타입 | 핵심 책임 |
|---|---|---|
| `Simulation_Input_Builder` | Builder | 요구사항, 선택 팀, 직원 snapshot, risk summary를 하나의 packet으로 병합 |
| `Privacy_and_Column_Filter` | Rule-based | 원천 개인정보/원문 데이터 제거, 업무 signal만 유지 |
| `Agent_Card_Builder` | Builder | 팀원별 Agent Card 생성 |
| `Scenario_Phase_Planner` | Rule-based + LLM | 프로젝트 phase와 phase별 agenda/event 생성 |
| `Simulation_Orchestrator` | LLM Agent | phase 진행, 발언 순서, 응답 형식 통제 |
| `Role Agents` | LLM Agents | 각 역할 관점에서 구조화 발언 생성 |
| `Phase_Log_Collector` | Logger | phase별 대화 요약, 발언, 이슈, 결정, action item 저장 |
| `Issue_Risk_Evaluator` | Rule-based + LLM | log와 risk signal을 기반으로 issue/risk 확정 |
| `Score_Calculator` | Rule-based | 지표별 점수와 overall project fit 계산 |

---

## 2. 권장 파일구조

```text
shadow_roleplay_agent/
  Final_shdow_roleplay_agent_implementation_plan.md
  shadow_roleplay_agent_implementatino_plan.md
  shadow_roleplay_agent_docs/
    README.md
    shadow_roleplay_agent_io_schema.md
    shadow_roleplay_agent_rules.md
    shadow_roleplay_agent_phase_flow.md
    shadow_roleplay_agent_phase_commands.md
    shadow_roleplay_agent_architecture_notes.md
    shadow_roleplay_agent_api_spec.md
    shadow_roleplay_agent_test_plan.md
    shadow_roleplay_agent_guardrails.md
```

실제 코드 구현 시 권장 구조:

```text
projectfit_ax/
  agents/
    shadow_roleplay_agent/
      prompts/
        simulation_orchestrator_prompt.md
        role_agent_prompt.md
        issue_risk_evaluator_prompt.md
      pipeline/
        shadow_roleplay_pipeline.py
        simulation_input_builder.py
        phase_runner.py
      modules/
        privacy_column_filter.py
        agent_card_builder.py
        scenario_phase_planner.py
        phase_log_collector.py
        issue_risk_evaluator.py
        score_calculator.py
      schemas/
        simulation_input_packet_schema.json
        agent_card_schema.json
        phase_log_schema.json
        simulation_output_schema.json
      tests/
        test_agent_card_builder.py
        test_phase_runner.py
        test_issue_risk_evaluator.py
        test_score_calculator.py
      samples/
        sample_requirements_list.json
        sample_selected_team_record.json
        sample_employee_fit_profile_snapshot.json
        sample_team_risk_summary.json
      outputs/
        Team_Simulation_Log.json
        Issue_Risk_Summary.json
        Simulation_OUTPUT.json
```

---

## 3. Input - Output 구조

### 3.1 최종 Input

| Input | 설명 | 사용 위치 |
|---|---|---|
| `Requirements_List.json` | 프로젝트 기능, 역할, 기술, 일정, 제약, 리스크 | project context, phase planning, scenario event |
| `Selected_Team_Record` | 선택된 팀 ID, 팀 순위, 팀 점수, 역할 배치 | simulation 대상 팀 정의 |
| `Employee_Fit_Profile_Snapshot` | 팀원별 역할, 스킬 매칭, capacity, delivery, communication signal | Agent Card 생성 |
| `Team_Risk_Summary` | 팀 단위 병목, 기술 gap, 일정, 협업 리스크 요약 | scenario event, issue prior |
| `Evidence_Metadata` | risk signal이 어떤 원천 column에서 왔는지 참조 | trigger_source, 설명 가능성 |

### 3.2 직접 사용하지 않는 Input

Shadow_RolePlay_Agent는 아래 데이터를 직접 읽지 않는다.

```text
Git 원천 DB
Jira 원천 DB
Slack 원문 메시지
Calendar 상세 일정
직원 실명/나이/성별/주소/개인 프로필
```

이 데이터들은 앞단 `Feature Engineering & Fit Scoring`에서 summary/signal/evidence로 변환된 뒤 Shadow Agent에 전달된다.

### 3.3 Intermediate Output

| Output | 생성 주체 | 설명 |
|---|---|---|
| `Simulation_Input_Packet.json` | Simulation_Input_Builder | simulation 실행에 필요한 입력 묶음 |
| `Sanitized_Profile_Snapshot.json` | Privacy_and_Column_Filter | 개인정보 제거 후 업무 signal만 남긴 snapshot |
| `Agent_Cards.json` | Agent_Card_Builder | A/B/C/D/E Agent Card |
| `Simulation_Phase_Plan.json` | Scenario_Phase_Planner | phase 순서, agenda, scenario event |
| `Phase_Log.json` | Phase_Log_Collector | phase별 구조화 로그 |
| `Issue_Candidates.json` | Issue_Risk_Evaluator | issue 후보 |
| `Score_Breakdown.json` | Score_Calculator | 지표별 점수 |

### 3.4 최종 Output

| Output | 설명 |
|---|---|
| `Team_Simulation_Log.json` | phase별 가상 프로젝트 진행 로그 |
| `Issue_Risk_Summary.json` | 발견된 issue, severity, evidence, root cause, mitigation |
| `Simulation_OUTPUT.json` | overall score, verdict, top risks, must-fix actions |

---

## 4. Simulation Phase

Shadow RolePlay의 실제 프로젝트 진행 phase는 5단계로 고정한다.

```text
Kickoff Meeting
→ Design Phase
→ Development Phase
→ Integration Phase
→ QA / Release Phase
```

| Phase | 확인 내용 | 근거 |
|---|---|---|
| Kickoff Meeting | 목표 이해, R&R, owner, 일정 인식 | 역할/책임 불명확성 조기 발견 |
| Design Phase | API, DB, 외부 의존성, 기술 선택 | 기술 복잡성과 설계 공백 확인 |
| Development Phase | 업무 분배, 구현 병목, 리뷰 흐름 | 일정/업무 집중 리스크 확인 |
| Integration Phase | FE/BE/API/DB 연동, 스펙 불일치 | 실제 충돌이 많이 드러나는 구간 |
| QA / Release Phase | 테스트 범위, 결함, release blocker | QA 누락과 릴리즈 리스크 확인 |

각 phase 실행 방식:

```text
Phase Brief
→ Agent별 1차 발언
→ 의존성/충돌 확인
→ Orchestrator 추가 질문
→ 결정사항 정리
→ Action Item 생성
→ Phase Log 저장
→ Phase Score 계산
```

---

## 5. Orchestrator 응답 형식

각 Role Agent는 아래 구조로만 응답한다.

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

이 형식은 자유 대화의 산만함을 줄이고, 모든 발언을 issue/risk/action/score로 변환하기 위한 구조다.

---

## 6. Issue/Risk 평가 Rule

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

최종 issue score:

```text
final_issue_score = 0.4 * pre_simulation_risk
                  + 0.6 * observed_simulation_risk
```

판단 근거:

- `pre_simulation_risk`는 앞단 fit scoring에서 생성된 risk signal이다.
- `observed_simulation_risk`는 해당 프로젝트 phase에서 실제로 관찰된 concern/dependency/unresolved issue다.
- DB 기반 가설보다 simulation에서 관찰된 결과를 더 중요하게 반영한다.

---

## 7. Score 산출

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

Verdict:

| Verdict | 의미 |
|---|---|
| `proceed` | 큰 보완 없이 진행 가능 |
| `proceed_with_conditions` | 보완 조치 후 진행 권장 |
| `needs_rebalancing` | 역할/업무량 재조정 필요 |
| `not_recommended` | 해당 프로젝트에는 리스크가 큼 |

---

## 8. Phase 단계별 구현 계획

### Phase 0. Input Contract & Sample 준비

필수 입력 schema와 샘플 데이터를 준비한다.

### Phase 1. Simulation Input Builder

Requirements, team, employee snapshot, risk summary, evidence metadata를 하나의 `Simulation_Input_Packet.json`으로 병합한다.

### Phase 2. Privacy & Column Filter

직원 실명, 원문 메시지, 상세 일정, 개인 프로필을 제거하고 업무 signal만 유지한다.

### Phase 3. Agent Card Builder

팀원별 직원 이름을 그대로 사용하는 Agent Card를 생성한다.

### Phase 4. Scenario Phase Planner

5개 phase와 phase별 agenda, scenario event, trigger_source를 생성한다.

### Phase 5. Simulation Orchestrator

phase 진행, Role Agent 발언 순서, 응답 형식, 재질문 규칙을 통제한다.

### Phase 6. Role Agent Execution

각 Role Agent가 자신의 Agent Card와 현재 phase context에 근거해 구조화 발언을 생성한다.

### Phase 7. Phase Log Collector

conversation summary, participant turns, trigger source, decision, action item, unresolved question을 저장한다.

### Phase 8. Issue/Risk Evaluator

structured log와 risk signal을 기반으로 issue/risk를 확정한다.

### Phase 9. Score Calculator

issue/risk를 지표별 점수로 변환하고 overall project fit을 계산한다.

### Phase 10. Recommendation Adjuster & Output Builder

simulation verdict, must-fix action, 추천 순위 보정 결과를 생성하고 최종 output을 저장한다.

---

## 9. Phase별 작업 지시 요청 멘트 및 필수 참조 파일

### Phase 0. Input Contract & Sample 준비

작업 지시 요청 멘트:

```text
Shadow_RolePlay_Agent 구현을 시작하기 위해 필요한 input schema와 sample 데이터를 준비해줘.
Requirements_List.json, Selected_Team_Record, Employee_Fit_Profile_Snapshot, Team_Risk_Summary, Evidence_Metadata의 필수 필드와 예시를 정의해줘.
```

필수 참조 파일:

```text
Final_shdow_roleplay_agent_implementation_plan.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
requirements_agent/requirements_agent_docs/requirements_agent_io_schema.md
```

### Phase 1. Simulation Input Builder

작업 지시 요청 멘트:

```text
Requirements_List.json, Selected_Team_Record, Employee_Fit_Profile_Snapshot, Team_Risk_Summary, Evidence_Metadata를 하나의 Simulation_Input_Packet.json으로 병합하는 Simulation_Input_Builder를 구현해줘.
각 risk와 agent 발언이 어떤 evidence에서 왔는지 추적 가능해야 해.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
```

### Phase 2. Privacy & Column Filter

작업 지시 요청 멘트:

```text
Shadow RolePlay 입력에서 직원 실명, 원문 Slack 메시지, 상세 Calendar 일정, 개인 프로필을 제거하고,
역할, 스킬, capacity, delivery, communication, risk_tags, evidence_refs만 남기는 Privacy_and_Column_Filter를 구현해줘.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
```

### Phase 3. Agent Card Builder

작업 지시 요청 멘트:

```text
팀원별 Employee_Fit_Profile_Snapshot을 기반으로 직원 이름을 그대로 사용하는 Agent Card를 생성하는 Agent_Card_Builder를 구현해줘.
Agent Card에는 assigned_role, responsibilities, strengths, constraints, risk_tags, evidence_refs, speaking_rules가 포함되어야 해.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
```

### Phase 4. Scenario Phase Planner

작업 지시 요청 멘트:

```text
Requirements_List와 Team_Risk_Summary를 기반으로 Kickoff, Design, Development, Integration, QA/Release 5개 phase의 agenda와 scenario_event를 생성하는 Scenario_Phase_Planner를 구현해줘.
각 scenario_event에는 trigger_source가 포함되어야 해.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_rules.md
Token_limit_Verify_phase.md
```

### Phase 5. Simulation Orchestrator

작업 지시 요청 멘트:

```text
각 phase의 진행 순서, Role Agent 발언 순서, 응답 형식, 재질문 규칙을 통제하는 Simulation_Orchestrator를 구현해줘.
Agent 발언은 observation, concern, dependency, proposed_action 형식으로만 저장되도록 강제해줘.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
```

### Phase 6. Role Agent Execution

작업 지시 요청 멘트:

```text
각 Role Agent가 자신의 Agent Card와 현재 phase context에 근거해 발언하도록 Role Agent 실행 로직을 구현해줘.
Agent는 주어진 evidence 밖의 개인정보나 사실을 생성하면 안 되고, 역할 관점에서 observation, concern, dependency, proposed_action만 반환해야 해.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
Agent_Cards.json
Simulation_Phase_Plan.json
```

### Phase 7. Phase Log Collector

작업 지시 요청 멘트:

```text
phase별 conversation_summary, participant_turns, trigger_source, detected_issues, decisions, action_items, unresolved_questions, phase_scores를 저장하는 Phase_Log_Collector를 구현해줘.
raw_dialogue는 선택 저장으로 두고, 기본은 구조화 로그 중심으로 저장해줘.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_io_schema.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_phase_flow.md
```

### Phase 8. Issue/Risk Evaluator

작업 지시 요청 멘트:

```text
structured phase log와 Team_Risk_Summary를 기반으로 role_conflict, schedule_risk, integration_risk, qa_coverage_gap 등 issue/risk를 확정하는 Issue_Risk_Evaluator를 구현해줘.
issue는 evidence와 simulation log 근거가 있을 때만 확정해줘.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_rules.md
shadow_roleplay_agent_docs/shadow_roleplay_agent_guardrails.md
Team_Simulation_Log.json
Team_Risk_Summary.json
```

### Phase 9. Score Calculator

작업 지시 요청 멘트:

```text
Issue_Risk_Summary를 기반으로 schedule_stability, role_clarity, technical_risk_control, integration_readiness, collaboration_quality, qa_release_readiness, workload_balance 점수를 계산하는 Score_Calculator를 구현해줘.
최종 overall_project_fit은 정의된 가중치 공식을 따라 계산해줘.
```

필수 참조 파일:

```text
shadow_roleplay_agent_docs/shadow_roleplay_agent_rules.md
Issue_Risk_Summary.json
```

---

## 10. Output 관리 방법

출력은 `project_id + team_id + simulation_id` 기준으로 관리한다.

```text
shadow_roleplay_agent/
  outputs/
    project_001/
      team_001/
        sim_001/
          00_input/
            Simulation_Input_Packet.json
            Sanitized_Profile_Snapshot.json
          01_agent_cards/
            Agent_Cards.json
          02_phase_plan/
            Simulation_Phase_Plan.json
          03_logs/
            Team_Simulation_Log.json
          04_issue_risk/
            Issue_Risk_Summary.json
          05_score/
            Score_Breakdown.json
          06_final/
            Simulation_OUTPUT.json
```

관리 원칙:

- 중간 산출물을 보존해 issue/risk 판단 근거를 추적한다.
- raw dialogue는 선택 저장으로 두고, 기본은 structured log를 사용한다.
- 후속 Report Files에는 final output과 핵심 summary만 전달한다.
- 직원 개인정보와 원문 업무 데이터는 output에 포함하지 않는다.

---

## 11. GCP 구현 위치

| GCP 서비스 | 사용 위치 |
|---|---|
| Cloud Run | Shadow RolePlay API 서버 |
| Vertex AI Gemini | Orchestrator, Role Agents, Issue summary |
| Firestore | Simulation Log, Issue Summary, Score 저장 |
| Cloud Storage | JSON output, Report Files 저장 |
| Cloud Logging | 실행 로그, 오류 기록 |

---

## 12. API 설계 초안

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

---

## 13. 테스트 시나리오

| 테스트 | 기대 결과 |
|---|---|
| 결제 API 포함 프로젝트 | Integration risk와 QA failure-case gap 탐지 |
| 특정 Backend에게 업무 집중 | workload concentration 상승 |
| QA role이 약한 팀 | qa_coverage_gap 상승 |
| 응답 지연 signal 높은 팀 | communication_delay 상승 |
| 모든 phase에서 unresolved high issue 없음 | `proceed` 또는 `proceed_with_conditions` |
| high issue가 QA/Release에 남음 | `needs_rebalancing` 또는 `not_recommended` |
| 개인정보가 포함된 snapshot 입력 | Privacy filter가 제거 |
| evidence 없는 concern 생성 | Orchestrator가 재질문 또는 invalid 처리 |

---

## 14. Acceptance Criteria

- 원천 Git/Jira/Slack/Calendar DB를 직접 읽지 않는다.
- snapshot/summary/evidence 기반으로 Agent Card를 생성한다.
- 5개 phase가 순서대로 실행된다.
- Agent 발언은 구조화 형식으로 저장된다.
- issue는 evidence와 simulation log가 있을 때 확정된다.
- 최종 output은 추천 결과 보정까지 연결된다.
- 최종 점수는 사람 평가 점수가 아니라 프로젝트 조건에서의 팀 조합 안정성 점수로 표시된다.

---

## 15. MVP 구현 우선순위

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

---

## 16. 최종 요약

Shadow_RolePlay_Agent는 추천된 팀 조합을 실제 프로젝트 진행 관점에서 검증하는 simulation layer다.

이 Agent는 사람을 평가하지 않는다.  
원천 업무 DB를 직접 읽지 않고, 앞단에서 생성된 snapshot, summary, evidence를 기반으로 Agent Card를 만들고, 현업 SDLC를 압축한 5개 phase에서 프로젝트 진행 과정을 관찰한다.

최종적으로 이 Agent는 아래 질문에 답한다.

```text
이 팀 조합은 점수상으로 좋아 보이지만,
실제 프로젝트를 시작하면 어디서 문제가 생길 수 있는가?
```

따라서 ProjectFit AX는 단순 팀 추천을 넘어, 착수 전 팀 조합의 실행 가능성과 프로젝트 리스크를 설명 가능한 방식으로 제시할 수 있다.
