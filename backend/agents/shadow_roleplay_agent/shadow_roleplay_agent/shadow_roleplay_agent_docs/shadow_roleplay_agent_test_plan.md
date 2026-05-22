# Shadow_RolePlay_Agent Test Plan

## 1. 목적

이 문서는 Shadow_RolePlay_Agent의 테스트 시나리오, edge case, acceptance criteria를 정의한다.

## 2. 주요 테스트 시나리오

| 테스트 | 입력 조건 | 기대 결과 |
|---|---|---|
| 결제 API 포함 프로젝트 | Requirements에 결제/외부 API 리스크 포함 | Integration risk와 QA failure-case gap 탐지 |
| 특정 Backend에게 업무 집중 | Team_Risk_Summary에 workload concentration | workload_concentration 상승 |
| QA role이 약한 팀 | QA coverage 낮음 | qa_coverage_gap 상승 |
| 응답 지연 signal 높은 팀 | communication_signal high delay | communication_delay 상승 |
| 안정적인 팀 | unresolved high issue 없음 | `proceed` 또는 `proceed_with_conditions` |
| 릴리즈 blocker 존재 | QA/Release phase에 high issue 남음 | `needs_rebalancing` 또는 `not_recommended` |
| 개인정보 포함 snapshot | name/email/raw message 포함 | Privacy filter가 제거 |
| evidence 없는 concern | Role Agent가 근거 없는 우려 생성 | Orchestrator가 재질문 또는 invalid 처리 |

## 3. Rule별 테스트

| Rule | 테스트 포인트 |
|---|---|
| Privacy Filter | 원천 개인 정보가 제거되는가 |
| Agent Card | 역할/책임/제약/evidence가 포함되는가 |
| Orchestrator | 응답 형식을 강제하는가 |
| Phase Planner | 5개 phase가 순서대로 생성되는가 |
| Log Collector | structured log가 저장되는가 |
| Issue Evaluator | evidence 있는 issue만 확정하는가 |
| Score Calculator | 가중치 공식대로 계산하는가 |
| Recommendation Adjuster | verdict와 rank 보정이 생성되는가 |

## 4. Acceptance Criteria

- 원천 Git/Jira/Slack/Calendar DB를 직접 읽지 않는다.
- snapshot/summary/evidence 기반으로 Agent Card를 생성한다.
- 5개 phase가 순서대로 실행된다.
- Agent 발언은 구조화 형식으로 저장된다.
- issue는 evidence와 simulation log가 있을 때 확정된다.
- 최종 output은 추천 결과 보정까지 연결된다.
- 최종 점수는 사람 평가 점수가 아니라 프로젝트 조건에서의 팀 조합 안정성 점수로 표시된다.
