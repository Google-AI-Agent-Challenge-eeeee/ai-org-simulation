# 1st Requirements And RolePlay Matching Implementation Plan

## 1. 문서 목적

이 문서는 `Requirements Agent -> ranking/team composition module -> Shadow RolePlay Agent` 흐름을 실제로 의미 있게 연결하기 위한 1차 보완 작업 계획이다.

현재 파이프라인은 파일 생성과 schema validation은 통과하지만, Shadow RolePlay 단계에서 risk tag가 scenario event로 충분히 변환되지 않아 실제 simulation turn이 비어 있을 수 있다. 이 문서는 API 연동을 제외하고, 로컬 실행 기준으로 role/risk/evidence/team coverage 연결을 보강하는 작업 범위를 정의한다.

## 2. 이번 작업 범위

포함:

- Requirements 산출물의 role/risk/skill/constraint를 Shadow RolePlay가 이해할 수 있는 표준 형태로 매핑
- ranking/team module이 PRD에 필요한 후보만 shortlist하고 팀 조합을 만들도록 강화
- RolePlay scenario planner가 risk tag를 event로 변환하지 못할 때 fallback event를 생성
- risk tag별 evidence metadata 보강
- selected team의 required role coverage gap 명시
- Requirements -> ranking -> RolePlay end-to-end 검증 테스트 추가

제외:

- FastAPI endpoint 구현
- Cloud DB / Firestore / Storage 연동
- 배포, 인증, 권한, infra 설정
- 실제 LLM 대화 품질 개선

## 3. 현재 확인된 문제점

| ID | 문제 | 영향 | 우선순위 |
|---|---|---|---|
| P1 | Requirements/ranking risk tag와 RolePlay scenario template risk tag가 다름 | `scenario_event_count=0`, 실제 roleplay turn 미발생 | High |
| P2 | Scenario planner에 generic fallback event가 없음 | template이 없는 risk는 simulation에서 사라짐 | High |
| P3 | 일부 `Team_Risk_Summary.risk_tags`에 대응 evidence가 없음 | issue 확정 근거 부족 | High |
| P4 | selected team이 일부 required role을 커버하지 못함 | 해당 역할 관점의 simulation 누락 | High |
| P5 | required role이 넓게 추출되면 ranking 후보군이 과도하게 넓어짐 | 핵심 후보 shortlist 가독성 저하 | Medium |
| P6 | Shadow RolePlay 전용 e2e 테스트 부족 | 빈 simulation이 성공처럼 보일 수 있음 | High |
| P7 | Shadow RolePlay lint 미정리 | CI/품질 기준 미충족 가능 | Medium |

## 4. 목표 상태

완료 후 목표:

- Requirements Agent가 만든 risk/role/skill이 RolePlay에서 바로 사용 가능한 canonical issue category로 연결된다.
- `Simulation_Phase_Plan.json`에는 최소 1개 이상의 meaningful scenario event가 존재한다.
- Role Agent turn이 생성되고 `Team_Simulation_Log.json`에 structured log가 남는다.
- `Issue_Risk_Summary.json`는 evidence 기반 issue/candidate를 생성한다.
- `Simulation_OUTPUT.json`은 빈 simulation이 아니라 실제 관찰 로그 기반 verdict를 낸다.
- selected team이 커버하지 못한 required role은 output에 명시되고 team score에 penalty로 반영된다.

## 5. Phase별 구현 계획

## Phase 1. Risk Taxonomy Bridge 추가

목표:

Requirements/ranking 쪽 risk tag를 Shadow RolePlay issue category 및 scenario template으로 연결한다.

작업:

- `requirements_agent` 또는 shared module에 risk bridge mapping 추가
- 예시 매핑:

| Source Risk Tag | Canonical Issue Category | RolePlay Event Family |
|---|---|---|
| `delivery_delay` | `schedule_risk` | schedule fallback |
| `security_and_compliance_issues` | `technical_dependency_risk` | technical/security fallback |
| `security_regression` | `qa_coverage_gap` | QA/security test fallback |
| `duplicate_notifications` | `integration_risk` | FE/BE/API integration fallback |
| `notification_fatigue` | `unclear_ownership` | product/UX ownership fallback |
| `mobile_permission_handling_issues` | `technical_dependency_risk` | mobile permission fallback |
| `offline_or_background_sync_issue` | `integration_risk` | background sync fallback |
| `missing_skill` | `technical_dependency_risk` | skill gap fallback |

완료 기준:

- RolePlay planner가 source risk tag를 canonical category로 해석할 수 있다.
- template이 있는 risk는 기존 template을 사용한다.
- template이 없는 risk도 canonical category 기반 fallback으로 event가 생성된다.

## Phase 2. Scenario Event Fallback 구현

목표:

RolePlay planner가 risk tag template을 못 찾더라도 simulation event를 생성한다.

작업:

- `ScenarioPhasePlanner`에 fallback event builder 추가
- fallback source:
  - `Team_Risk_Summary.risk_tags`
  - `risk_prior_scores`
  - `Evidence_Metadata`
  - `RequirementsList.constraints`
  - selected team role coverage gap
  - member `missing_skills`
- phase별 fallback routing:

| Canonical Category | Preferred Phase |
|---|---|
| `schedule_risk` | Kickoff, Development |
| `technical_dependency_risk` | Design, Development |
| `integration_risk` | Integration |
| `qa_coverage_gap` | QA / Release |
| `communication_delay` | Kickoff, QA / Release |
| `workload_concentration` | Development |
| `unclear_ownership` | Kickoff |
| `role_conflict` | Kickoff, Design |
| `release_blocker` | QA / Release |

완료 기준:

- e2e 실행 시 `scenario_event_count > 0`
- 각 event는 `trigger_source`, `involved_roles`, `expected_issue_category`를 가진다.
- fallback event도 문서의 structured simulation format을 따른다.

## Phase 3. Evidence Metadata 보강

목표:

RolePlay에서 사용하는 모든 주요 risk tag에 최소 1개 이상의 evidence reference를 제공한다.

작업:

- `employee_team_ranking.py`의 evidence 생성 로직 보강
- evidence source 우선순위:
  1. selected employee source column
  2. `requirements_list.risk_factors.source_feature_keys`
  3. `requirements_list.constraints`
  4. `requirements_list.required_features`
  5. fallback source column marker: `requirements.risk_factors`
- evidence 없는 risk tag는 `evidence_gap`으로 별도 표시

완료 기준:

- `Team_Risk_Summary.risk_tags` 중 evidence 없는 항목 수가 0 또는 명시적 `evidence_gap`으로 표시된다.
- Issue/Risk Evaluator가 evidence 기반 판단을 수행할 수 있다.

## Phase 4. Required Role Coverage 정책 강화

목표:

selected team이 PRD required role을 얼마나 커버하는지 명확히 하고, 누락 역할을 simulation에 반영한다.

작업:

- required role을 `must`, `should`, `support`로 분류하는 helper 추가
- selected team output에 `covered_required_roles`, `uncovered_required_roles` 추가 검토
- team ranking score에 uncovered role penalty 강화
- RolePlay handoff manifest에 role coverage gap 추가
- uncovered role이 있으면 planner에 `unclear_ownership` 또는 `role_coverage_gap` event 생성

완료 기준:

- selected team이 모든 must role을 커버하거나, 미커버 이유가 명시된다.
- 미커버 role이 simulation event로 전달된다.

## Phase 5. Ranking Payload Shortlist 구조 개선

목표:

전체 후보군과 실제 RolePlay/팀 추천에 쓰는 shortlist를 분리한다.

작업:

- `Employee_Fit_Ranking.json`에 아래 구조 추가:
  - `candidate_scope`
  - `role_candidate_counts`
  - `shortlisted_candidates_by_role`
  - `excluded_employee_count`
  - `used_employee_columns`
- role별 top N 후보 중심으로 출력 가독성 개선
- full candidate pool이 필요하면 내부 계산에만 유지

완료 기준:

- 사용자가 PRD별 핵심 후보를 바로 확인할 수 있다.
- team composition은 shortlist 또는 명시된 candidate pool에서만 생성된다.

## Phase 6. End-to-End Validation Test 추가

목표:

빈 simulation이 성공처럼 보이지 않도록 테스트한다.

추가 테스트:

- Requirements local runner -> ranking bridge -> RolePlay input packet schema validation
- RolePlay planner scenario event 생성
- Orchestrator role turn 생성
- Team simulation log 생성
- Issue/Risk summary 생성
- Simulation output 생성

필수 assertion:

- `scenario_event_count > 0`
- `orchestrator_phase_run_count > 0`
- `team_simulation_phase_log_count > 0`
- `Roleplay_Simulation_Input_Packet` schema valid
- selected team members are all from ranked candidates
- uncovered required roles are explicit if any

## Phase 7. Shadow RolePlay Lint 정리

목표:

`backend/agents` 기준 lint를 통과시킨다.

작업:

- import 정렬
- unused import 제거
- unused variable 제거
- type annotation quote 제거
- `Union` -> `|` 변환

완료 기준:

- `python -m ruff check backend/agents backend/tests/test_requirements_agent_*.py` 통과
- 기존 tests 전체 통과

## 6. 작업 순서

권장 순서:

1. Risk Taxonomy Bridge 추가
2. Scenario Event Fallback 구현
3. Evidence Metadata 보강
4. Required Role Coverage 정책 강화
5. Ranking Payload Shortlist 구조 개선
6. RolePlay e2e 테스트 추가
7. Shadow RolePlay lint 정리
8. 로컬 PRD로 최종 e2e 실행

## 7. 최종 검증 명령

```powershell
.venv\Scripts\python.exe -m compileall -q backend\agents
.venv\Scripts\python.exe -m ruff check backend\agents backend\tests\test_requirements_agent_*.py
.venv\Scripts\python.exe -m pytest backend\tests -q
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" --employee-data-dir "datasets/raw" --llm-mode stub --write-outputs
```

## 8. 완료 판단 기준

이 작업은 아래 조건이 모두 충족되면 완료로 본다.

- Requirements Agent output이 ranking/team module에 schema 오류 없이 입력된다.
- ranking/team module이 PRD required role 기반 후보와 팀 조합을 생성한다.
- RolePlay input 5종과 `SimulationInputPacket`이 모두 schema validation을 통과한다.
- Shadow RolePlay planner가 1개 이상의 scenario event를 생성한다.
- Orchestrator가 Role Agent turn을 생성한다.
- Issue/Risk Evaluator가 evidence/log 기반 issue summary를 생성한다.
- Final `Simulation_OUTPUT.json`이 빈 simulation이 아닌 관찰 기반 verdict를 제공한다.
