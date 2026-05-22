# Shadow_RolePlay_Agent Phase Flow

## 1. 전체 Phase Flow

```text
Phase 0. Input Contract & Sample 준비
→ Phase 1. Simulation Input Builder
→ Phase 2. Privacy & Column Filter
→ Phase 3. Agent Card Builder
→ Phase 4. Scenario Phase Planner
→ Phase 5. Simulation Orchestrator
→ Phase 6. Role Agent Execution
→ Phase 7. Phase Log Collector
→ Phase 8. Issue/Risk Evaluator
→ Phase 9. Score Calculator
→ Phase 10. Recommendation Adjuster & Output Builder
```

## 2. Phase별 요약

| Phase | 목적 | 주요 Input | 주요 Output |
|---|---|---|---|
| Phase 0 | input schema와 sample 준비 | implementation plan | sample input set |
| Phase 1 | simulation 입력 병합 | requirements/team/snapshot/risk/evidence | Simulation_Input_Packet |
| Phase 2 | 개인정보 및 원문 제거 | input packet | Sanitized_Profile_Snapshot |
| Phase 3 | Agent Card 생성 | sanitized snapshot | Agent_Cards |
| Phase 4 | phase plan 생성 | requirements, team risk | Simulation_Phase_Plan |
| Phase 5 | simulation 진행 통제 | phase plan, agent cards | orchestrated turns |
| Phase 6 | Role Agent 발언 생성 | agent card, phase context | participant turns |
| Phase 7 | phase log 저장 | participant turns | Team_Simulation_Log |
| Phase 8 | issue/risk 확정 | structured log, risk summary | Issue_Risk_Summary |
| Phase 9 | score 계산 | issue summary | Score_Breakdown |
| Phase 10 | 추천 보정 및 output 생성 | score, team rank, issue summary | final outputs |

## 3. Phase 0. Input Contract & Sample 준비

구현 항목:

- input schema 정의
- sample `Requirements_List.json`
- sample `Selected_Team_Record`
- sample `Employee_Fit_Profile_Snapshot`
- sample `Team_Risk_Summary`
- sample `Evidence_Metadata`

점검사항:

- 원천 Git/Jira/Slack/Calendar DB가 직접 input에 포함되지 않았는가
- 직원 이름이 포함됐는가
- evidence_refs가 포함됐는가

## 4. Phase 1. Simulation Input Builder

구현 항목:

- 입력 5종 병합
- project context 구성
- selected team 구성
- member snapshot 연결
- evidence metadata 연결

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

## 5. Phase 2. Privacy & Column Filter

구현 항목:

- 개인정보 제거
- 원문 메시지 제거
- 상세 일정 제거
- 업무 signal만 유지

유지:

```text
assigned_role
matched_skills
missing_skills
capacity_signal
communication_signal
delivery_signal
collaboration_signal
risk_tags
evidence_refs
```

## 6. Phase 3. Agent Card Builder

구현 항목:

- 팀원별 Agent Card 생성
- speaking_rules 부여
- responsibilities 구성
- constraints/risk_tags 연결

점검사항:

- 실제 사람의 복제처럼 표현하지 않았는가
- 개인정보가 포함되지 않았는가
- evidence_refs가 유지되는가

## 7. Phase 4. Scenario Phase Planner

고정 phase:

```text
Kickoff Meeting
Design Phase
Development Phase
Integration Phase
QA / Release Phase
```

구현 항목:

- phase별 agenda 생성
- scenario_event 생성
- trigger_source 연결

## 8. Phase 5. Simulation Orchestrator

구현 항목:

- phase 진행 순서 통제
- Role Agent 발언 순서 통제
- 응답 형식 강제
- 근거 없는 발언 재질문

응답 형식:

```json
{
  "observation": "",
  "concern": "",
  "dependency": "",
  "proposed_action": ""
}
```

## 9. Phase 6. Role Agent Execution

구현 항목:

- Agent Card 기반 발언 생성
- 현재 phase context만 사용
- evidence 밖의 사실 생성 금지

## 10. Phase 7. Phase Log Collector

저장 항목:

```text
conversation_summary
participant_turns
trigger_source
detected_issues
decisions
action_items
unresolved_questions
phase_scores
```

## 11. Phase 8. Issue/Risk Evaluator

구현 항목:

- structured log 분석
- issue/risk 후보 생성
- evidence 기반 issue 확정
- severity/status/root cause/mitigation 생성

## 12. Phase 9. Score Calculator

구현 항목:

- 지표별 점수 계산
- overall project fit 계산
- score breakdown 생성

## 13. Phase 10. Recommendation Adjuster & Output Builder

구현 항목:

- verdict 산출
- must-fix action 생성
- 추천 순위 보정
- final outputs 저장
