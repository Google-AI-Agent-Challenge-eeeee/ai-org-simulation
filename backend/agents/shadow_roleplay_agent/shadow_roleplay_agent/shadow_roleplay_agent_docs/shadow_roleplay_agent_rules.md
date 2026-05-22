# Shadow_RolePlay_Agent Rules

## 1. 목적

이 문서는 Shadow_RolePlay_Agent의 issue/risk 평가 rule, score 계산, verdict 판단 기준을 정의한다.

## 2. Issue/Risk 지표

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

## 3. Issue 확정 Rule

최종 issue 판단은 pre-simulation risk와 observed simulation risk를 결합한다.

```text
final_issue_score = 0.4 * pre_simulation_risk
                  + 0.6 * observed_simulation_risk
```

근거:

- `pre_simulation_risk`는 앞단 fit scoring에서 생성된 가능성이다.
- `observed_simulation_risk`는 해당 프로젝트 phase에서 실제로 관찰된 로그다.
- Shadow RolePlay는 검증 계층이므로 관찰 결과에 더 높은 비중을 둔다.

## 4. 지표별 분석 기준

| 지표 | 분석 기준 |
|---|---|
| `role_conflict` | 동일 기능에 owner가 중복되거나 Agent들이 책임을 다르게 해석 |
| `unclear_ownership` | action item 또는 feature에 owner가 없음 |
| `schedule_risk` | 일정 제약, capacity risk, unresolved dependency가 함께 발생 |
| `workload_concentration` | action item, dependency, responsibility가 특정 Agent에 집중 |
| `technical_dependency_risk` | missing skill, 외부 API, 신규 기술, scope change가 관찰 |
| `integration_risk` | API/DB/schema/environment dependency가 Integration phase에 남음 |
| `communication_delay` | 동일 질문/결정 지연이 여러 phase에서 반복 |
| `qa_coverage_gap` | high-risk feature의 성공/실패/예외 테스트가 누락 |
| `release_blocker` | QA/Release 종료 시점에 unresolved high issue 존재 |

## 5. Score 계산

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

## 6. Verdict Rule

| Verdict | 기준 |
|---|---|
| `proceed` | overall score 높고 unresolved high issue 없음 |
| `proceed_with_conditions` | 진행 가능하지만 must-fix action 존재 |
| `needs_rebalancing` | 특정 role/workload/ownership 재조정 필요 |
| `not_recommended` | critical issue 또는 release blocker가 해소되지 않음 |

## 7. Evidence Rule

Issue는 아래 중 최소 1개 이상의 근거를 가져야 한다.

```text
Team_Risk_Summary risk tag
Evidence_Metadata reference
Phase Log concern
Phase Log dependency
unresolved_question
action_item owner gap
QA/Release unresolved high issue
```

근거 없는 issue는 최종 issue로 확정하지 않는다.
