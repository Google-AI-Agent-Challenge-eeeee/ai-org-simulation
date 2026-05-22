# Shadow_RolePlay_Agent Guardrails

## 1. 목적

이 문서는 Shadow_RolePlay_Agent 구현 시 개인정보, hallucination, 근거 없는 리스크 생성, score 오해를 줄이기 위한 guardrail을 정의한다.

## 2. 개인정보 Guardrail

금지 input:

```text
나이
성별
주소
학교
Slack 원문 메시지
Calendar 상세 일정
Jira/Slack 사용자 프로필 원문
```

허용 input:

```text
employee_name
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

## 3. Agent 발언 Guardrail

Role Agent는 **그 사람 자체의 시뮬레이션**이다.  
페르소나는 역할 단위가 아니라 이름을 가진 실제 팀원이다.

Role Agent가 지켜야 할 규칙:

```text
자신의 역할·담당 업무 관점에서 발언한다
자신의 협업 성향(collaboration_signal)에 맞는 말투를 사용한다
동료를 부를 때 이름으로 호칭한다 (예: "권원솔 씨", "안우빈 씨")
근거(evidence_refs)가 있는 사실만 인용한다
발언은 observation, concern, dependency, proposed_action 구조로 반환한다
```

허용:

- 개인 성격, 감정, 의견 표현 (역할·신호 데이터에서 파생된 범위)
- 동료 이름으로 직접 호칭
- 자신의 리스크 상황에 따른 불안, 불만, 강조 표현

금지:

- 원천 DB(Git/Jira/Slack 원문)에 없는 사실 생성
- 재미를 위한 갈등·드라마 연출
- evidence 없는 issue 확정
- 나이·성별·주소·학교 등 PII 참조

## 4. Simulation Guardrail

원칙:

- RolePlay는 자유 대화가 아니다.
- Orchestrator가 phase, agenda, event, output format을 통제한다.
- phase는 Kickoff, Design, Development, Integration, QA/Release 순서를 따른다.
- 각 phase 결과는 structured log로 저장한다.

## 5. Issue/Risk Guardrail

Issue 확정 조건:

```text
Team_Risk_Summary 또는 Evidence_Metadata에 근거가 있음
AND simulation log에서 concern/dependency/unresolved issue로 관찰됨
```

근거 없는 우려는 issue 후보로만 남기거나 invalid 처리한다.

## 6. Score Guardrail

최종 score는 사람 평가 점수가 아니다.

정확한 의미:

```text
해당 프로젝트 요구사항에서 선택된 팀 조합이 얼마나 안정적으로 프로젝트를 진행할 수 있는지에 대한 simulation 기반 프로젝트 적합도
```

금지 표현:

```text
A 직원은 70점이다
이 직원은 협업을 못한다
이 팀원은 성과가 낮다
```

권장 표현:

```text
이 팀 조합은 Integration Phase에서 API dependency risk가 관찰되었다
이 팀은 proceed_with_conditions이며, 시작 전 mock API schema 확정이 필요하다
```

## 7. Output Guardrail

최종 output에는 다음이 포함되어야 한다.

```text
simulation_verdict
overall_project_fit
score_breakdown
top_risks
must_fix_before_start
evidence summary
```

최종 output에는 다음이 포함되면 안 된다.

```text
원천 Slack 메시지
상세 Calendar 일정
나이·성별·주소·학교 등 PII
근거 없는 평가 표현
```
