# Shadow_RolePlay_Agent Architecture Notes

## 1. 핵심 정의

Shadow_RolePlay_Agent는 추천된 팀을 "좋아 보이는 조합"에서 끝내지 않고, 실제 프로젝트를 진행한다고 가정했을 때 어떤 리스크가 드러나는지 검증하는 Agent다.

핵심 질문:

```text
이 팀 조합은 점수상으로 좋아 보이지만,
실제 프로젝트를 시작하면 어디서 문제가 생길 수 있는가?
```

## 2. 세부 아키텍처

```text
[Input Layer]
Requirements_List.json
Selected_Team_Record
Employee_Fit_Profile_Snapshot
Team_Risk_Summary
Evidence_Metadata

→ [Simulation_Input_Builder]
→ [Privacy_and_Column_Filter]
→ [Agent_Card_Builder]
→ [Scenario_Phase_Planner]
→ [Simulation_Orchestrator]
→ [A/B/C/D/E Role Agents]
→ [Phase_Log_Collector]
→ [Issue_Risk_Evaluator]
→ [Score_Calculator]

→ [Output Layer]
Team_Simulation_Log.json
Issue_Risk_Summary.json
Simulation_OUTPUT.json
```

## 3. 왜 Persona가 필요한가

Persona는 사람 흉내를 내기 위한 장치가 아니다.

Agent Card는 아래 정보를 가진 프로젝트 역할 단위다.

```text
assigned_role
responsibilities
strengths
constraints
risk_tags
collaboration_signal
delivery_signal
evidence_refs
speaking_rules
```

필요한 이유:

- 정량 점수는 역할 간 상호작용을 보여주지 못한다.
- 프로젝트 진행 중 역할 충돌, 의존성, 일정 병목은 사람들의 역할 관계에서 드러난다.
- Agent Card는 이 상호작용을 데이터 기반으로 관찰하기 위한 simulation unit이다.

## 4. 원천 DB를 직접 넣지 않는 이유

Shadow Agent는 Git/Jira/Slack/Calendar 원천 DB를 직접 입력받지 않는다.

이유:

- 앞단 fit scoring에서 이미 사용했기 때문이다.
- 원천 메시지와 상세 일정은 개인정보/감시 오해를 만들 수 있다.
- RolePlay에는 원천 데이터가 아니라 프로젝트 진행에 영향을 주는 risk signal만 필요하다.
- evidence_refs만 남기면 설명 가능성과 개인정보 최소화를 동시에 확보할 수 있다.

## 5. 5개 Phase를 사용하는 이유

| Phase | 리스크가 드러나는 방식 |
|---|---|
| Kickoff | R&R, owner, 일정 인식 차이 |
| Design | API, DB, 외부 의존성, 기술 선택 문제 |
| Development | 업무 분배, 구현 병목, 리뷰 흐름 |
| Integration | FE/BE/API/DB 스펙 불일치 |
| QA / Release | 테스트 범위, 결함, release blocker |

5개 phase는 현업 SDLC를 MVP에 맞게 압축한 구조다.

## 6. Log 중심 설계 이유

Shadow RolePlay의 최종 가치는 대화 자체가 아니라 대화에서 추출되는 구조화 로그다.

저장해야 하는 log:

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

raw_dialogue는 선택 저장이다.

## 7. 최종 판단 방식

정량 적합도 점수는 "추천"을 만든다.  
Shadow RolePlay는 "추천 검증"을 수행한다.

최종 결과:

```text
proceed
proceed_with_conditions
needs_rebalancing
not_recommended
```

이 판단은 팀원 평가가 아니라 팀 조합의 프로젝트 안정성 판단이다.
