# 2nd Requirements And RolePlay Matching Implementation Plan

## 1. 목적

이 문서는 1차 구현으로 연결된 `Requirements Agent -> 직원/팀 ranking -> Shadow RolePlay Agent` 흐름을 MVP 아키텍처에 맞게 보완하기 위한 2차 작업 계획이다.

핵심 수정 방향은 다음과 같다.

```text
DB
-> preprocessing / feature engineering
-> compare
-> employee ranking
-> team composition
-> team ranking
-> roleplay input
-> roleplay simulation output
```

즉, feature engineering은 compare 전에 수행되는 별도 단계이고, compare는 ranking과 같은 단계가 아니라 ranking을 만들기 위한 요구사항-직원 feature 비교 단계다.

## 2. 1차 구현에서 확인된 상태

| 구분 | 상태 |
|---|---|
| PRD -> `Requirements_List.json` | 구현 및 실행 확인 |
| `Requirements_List.json` -> 직원별 ranking | 구현 및 실행 확인 |
| 직원별 ranking -> 팀 조합 ranking | 구현 및 실행 확인 |
| ranking/team -> RolePlay input packet | 구현 및 실행 확인 |
| RolePlay input packet -> `Simulation_OUTPUT.json` | 구현 및 실행 확인 |
| Human Confirm | JSON decision 방식은 구현됨. UI/API는 미구현 |
| DB -> Compare 전 feature engineering | 일부 로직이 ranking 내부에 섞여 있음. 별도 단계로 분리 필요 |

## 3. 현재 남은 주요 개선사항

| 우선순위 | 개선 항목 | 현재 상태 | 목표 상태 |
|---:|---|---|---|
| 1 | DB -> preprocessing / feature engineering 분리 | `employee_team_ranking.py` 내부에 join/normalize/scoring이 섞여 있음 | 별도 preprocessing module과 feature 산출물 생성 |
| 2 | preprocessing -> compare 단계 추가 | ranking 내부에서 requirements와 직원 feature를 바로 점수화 | `Requirements_Employee_Compare.json`으로 비교 결과를 명시 |
| 3 | compare -> employee ranking 분리 | compare와 ranking이 한 모듈 안에 섞여 있음 | compare 결과를 기반으로 직원 ranking 생성 |
| 4 | team composition / team ranking 분리 | 팀 생성과 팀 ranking이 한 모듈 안에 섞여 있음 | 후보군 구성과 팀 ranking 산출물을 명확히 분리 |
| 5 | feature schema / evidence trace 정리 | 내부 계산용 dict 중심 | feature별 source column, normalization method, missing policy 명시 |
| 6 | Human Confirm 사용성 | JSON decision 파일 수동 작성 | 로컬 decision template 생성/검증/적용 흐름 명확화 |
| 7 | RolePlay 로컬 실행 CLI | 긴 Python snippet으로 실행 | `run_shadow_roleplay_local.py` 추가 |
| 8 | end-to-end 검증 강화 | 테스트는 있으나 preprocessing/compare 분리 단계 없음 | PRD -> preprocessing -> compare -> ranking -> roleplay output까지 검증 |

## 4. 목표 아키텍처

```text
PRD
  -> Requirements Agent
  -> Requirements_List.json

datasets/raw
  -> Employee Feature Preprocessing
  -> Employee_Feature_Matrix.json
  -> Employee_Feature_Metadata.json

Requirements_List.json + Employee_Feature_Matrix.json
  -> Requirements-Employee Compare
  -> Requirements_Employee_Compare.json

Requirements_Employee_Compare.json
  -> Employee Ranking
  -> Employee_Fit_Ranking.json

Employee_Fit_Ranking.json + Requirements_List.json
  -> Team Composition
  -> Team_Composition_Candidates.json

Team_Composition_Candidates.json
  -> Team Ranking
  -> Team_Composition_Ranking.json

Top Team + Requirements_List.json + Evidence
  -> RolePlay Handoff Builder
  -> Roleplay_Simulation_Input_Packet.json

Roleplay_Simulation_Input_Packet.json
  -> Shadow RolePlay Agent
  -> Team_Simulation_Log.json
  -> Issue_Risk_Summary.json
  -> Score_Breakdown.json
  -> Simulation_OUTPUT.json
```

## 5. Output 파일 목표

| 단계 | 파일 | 설명 |
|---|---|---|
| preprocessing | `Employee_Feature_Matrix.json` | 직원별 정규화 feature matrix |
| preprocessing | `Employee_Feature_Metadata.json` | feature 생성 정책, source columns, normalization policy |
| compare | `Requirements_Employee_Compare.json` | requirements와 직원 feature 비교 결과 |
| employee ranking | `Employee_Fit_Ranking.json` | 직원별 프로젝트 적합도 순위 |
| team composition | `Team_Composition_Candidates.json` | 역할별 후보군으로 만든 팀 조합 후보 |
| team ranking | `Team_Composition_Ranking.json` | 팀 조합별 적합도/리스크/coverage 순위 |
| roleplay input | `Roleplay_Simulation_Input_Packet.json` | Shadow RolePlay 전체 입력 packet |
| roleplay output | `Simulation_OUTPUT.json` | 최종 팀 시뮬레이션 결과 |

## 6. Phase별 구현 계획

## Phase 1. Employee Feature Engineering 모듈 추가

### 목표

`datasets/raw`의 HR/GitHub/Slack/Jira/Calendar CSV를 join하고, compare 전에 사용할 직원 feature matrix를 생성한다.

### 생성/수정 파일

| 파일 | 작업 |
|---|---|
| `backend/agents/requirements_agent/modules/employee_feature_preprocessing.py` | 신규 생성 |
| `backend/agents/requirements_agent/schemas/employee_feature_matrix_schema.json` | 신규 생성 |
| `backend/tests/test_requirements_agent_employee_feature_preprocessing.py` | 신규 생성 |

### 구현 내용

- HR `employee_id` 기준으로 GitHub/Slack/Jira/Calendar 데이터 join
- UTF-8 BOM 처리
- numeric/string/enum column type 분류
- missing value policy 적용
- restricted/sensitive column 제외
- min-max normalization
- negative column inverse normalization
- role-relevant derived feature 생성
- feature별 evidence trace 생성
- role eligibility feature 생성

### 산출물

| 산출물 | 설명 |
|---|---|
| `Employee_Feature_Matrix.json` | 직원별 정규화 feature, role signal, evidence trace 포함 |
| `Employee_Feature_Metadata.json` | feature 생성 방식, source columns, normalization policy 포함 |

### 완료 기준

- 모든 직원 row가 하나의 feature profile로 생성된다.
- raw DB의 민감/제한 column이 직접 downstream으로 전달되지 않는다.
- 각 feature가 어떤 source column에서 왔는지 추적 가능하다.
- schema validation을 통과한다.

## Phase 2. Requirements-Employee Compare Module 추가

### 목표

`Requirements_List.json`의 요구 role/skill/risk/column weight와 `Employee_Feature_Matrix.json`를 비교해 직원별 비교 결과를 만든다.

이 단계는 ranking이 아니다. 직원별로 어떤 요구사항을 충족했고, 어떤 feature가 근거인지 비교표를 만드는 단계다.

### 생성/수정 파일

| 파일 | 작업 |
|---|---|
| `backend/agents/requirements_agent/modules/requirements_employee_compare.py` | 신규 생성 |
| `backend/agents/requirements_agent/schemas/requirements_employee_compare_schema.json` | 신규 생성 |
| `backend/tests/test_requirements_agent_requirements_employee_compare.py` | 신규 생성 |

### 구현 내용

- required roles와 employee role eligibility 비교
- required skills와 derived skill/role signal 비교
- selected employee columns와 feature matrix key 비교
- column weights 기반 weighted feature match 계산
- risk factors와 employee/team risk signal 연결
- compare evidence refs 기록
- ranking 전 intermediate score와 reason 생성

### 산출물

| 산출물 | 설명 |
|---|---|
| `Requirements_Employee_Compare.json` | 직원별 요구사항 충족/미충족/부분충족 비교 결과 |

### 완료 기준

- 직원별 compare result가 ranking 없이도 해석 가능하다.
- 각 compare score는 사용 feature와 source evidence를 포함한다.
- role mismatch, missing skill, missing feature는 명시적으로 표시된다.

## Phase 3. Employee Ranking Module 정리

### 목표

직원 ranking은 raw DB나 feature engineering을 직접 수행하지 않고, `Requirements_Employee_Compare.json`을 입력으로 받아 순위를 만든다.

### 수정 파일

| 파일 | 작업 |
|---|---|
| `backend/agents/requirements_agent/modules/employee_team_ranking.py` | employee ranking 입력을 compare result 기반으로 정리 |
| 신규 분리 가능: `backend/agents/requirements_agent/modules/employee_fit_ranking.py` | 직원 ranking 전용 모듈로 분리 가능 |
| `backend/tests/test_requirements_agent_employee_team_ranking.py` | compare 기반 ranking 테스트 보강 |

### 구현 내용

- compare score를 기반으로 employee fit score 계산
- role별 candidate pool 생성
- project-required role에 해당하지 않는 직원 제외
- `shortlisted_candidates_by_role` 생성
- excluded employee count 기록
- ranking reason과 evidence refs 유지

### 산출물

| 산출물 | 설명 |
|---|---|
| `Employee_Fit_Ranking.json` | 프로젝트 요구사항 대비 직원별 적합도 순위 |

### 완료 기준

- 직원 ranking은 compare result 없이 생성되지 않는다.
- 모든 ranking score는 compare result의 feature/evidence를 추적할 수 있다.
- 전체 직원이 아니라 PRD 필요 직군 후보만 ranking 대상이 된다.

## Phase 4. Team Composition / Team Ranking 분리

### 목표

직원 ranking 결과를 기반으로 팀 후보 조합을 만들고, 그 팀 후보들을 별도로 ranking한다.

### 생성/수정 파일

| 파일 | 작업 |
|---|---|
| 신규 분리 가능: `backend/agents/requirements_agent/modules/team_composition_builder.py` | 팀 후보 조합 생성 |
| 신규 분리 가능: `backend/agents/requirements_agent/modules/team_composition_ranking.py` | 팀 후보 ranking |
| `backend/agents/requirements_agent/modules/employee_team_ranking.py` | 기존 통합 wrapper 유지 또는 orchestration 역할로 축소 |

### 구현 내용

- required role slots 기준 팀 후보 생성
- 동일 employee 중복 방지
- role coverage 계산
- skill coverage 계산
- workload/risk concentration 계산
- critical dependency 계산
- team risk summary와 evidence metadata 생성

### 산출물

| 산출물 | 설명 |
|---|---|
| `Team_Composition_Candidates.json` | 가능한 팀 후보 조합 |
| `Team_Composition_Ranking.json` | 팀 후보별 최종 순위 |

### 완료 기준

- 팀 후보는 employee ranking에서 선별된 후보로만 구성된다.
- 팀 ranking은 개인 점수 평균이 아니라 role coverage, skill coverage, risk, availability를 함께 반영한다.
- selected team의 uncovered role이 있으면 명시적으로 downstream에 전달된다.

## Phase 5. Pipeline / Local Runner Output 연결

### 목표

로컬 실행 시 preprocessing, compare, ranking, team, roleplay handoff 산출물이 순서대로 생성되도록 한다.

### 수정 파일

| 파일 | 작업 |
|---|---|
| `backend/agents/requirements_agent/pipeline/run_requirements_agent_local.py` | preprocessing/compare/team outputs 연결 |
| `backend/agents/requirements_agent/pipeline/requirements_pipeline.py` | 필요 시 summary/output key 보강 |

### 추가 summary 필드

| 필드 | 설명 |
|---|---|
| `feature_preprocessing_ready` | feature matrix 생성 여부 |
| `feature_profile_count` | feature profile 직원 수 |
| `feature_key_count` | 생성 feature key 수 |
| `compare_result_count` | compare 대상 직원 수 |
| `employee_fit_candidate_count` | ranking 대상 직원 수 |
| `team_candidate_count` | 팀 후보 수 |
| `roleplay_simulation_input_ready` | RolePlay input packet 준비 여부 |

### 완료 기준

- `--write-outputs` 실행 시 preprocessing/compare/ranking/team/roleplay input 파일이 모두 생성된다.
- 실행 summary에서 각 단계별 count를 확인할 수 있다.

## Phase 6. Human Confirm 로컬 사용성 정리

### 목표

Human Confirm은 이미 JSON decision 방식으로 적용 가능하므로, 로컬 MVP에서 사용자가 쉽게 작성하고 검증할 수 있게 정리한다.

### 생성/수정 파일

| 파일 | 작업 |
|---|---|
| `backend/agents/requirements_agent/modules/human_confirm.py` | decision validation 보강 |
| `backend/agents/requirements_agent/local_inputs/human_confirm_decision_prd_001.json` | 템플릿 보강 |
| `backend/tests/test_requirements_agent_human_confirm.py` | decision 적용 테스트 보강 |

### 구현 내용

- unknown requirement mapping 예시 필드 정리
- removed item key 검증
- restricted column confirm 검증
- `human_confirm_complete=true`일 때 blocked final weighting이 풀리는지 확인

### 완료 기준

- decision 파일을 넣으면 `Requirements_List.json` 상태 변화가 명확하다.
- 전역 `taxonomy.json`은 수정되지 않는다.
- project-specific mapping만 적용된다.

## Phase 7. Shadow RolePlay 로컬 실행 CLI 추가

### 목표

긴 Python snippet 없이 RolePlay 최종 output까지 실행할 수 있게 한다.

### 생성 파일

| 파일 | 작업 |
|---|---|
| `backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/pipeline/run_shadow_roleplay_local.py` | 신규 생성 |
| `backend/tests/test_shadow_roleplay_local_runner.py` | 신규 생성 |

### CLI 예시

```powershell
.venv\Scripts\python.exe -m backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.run_shadow_roleplay_local --input-packet "backend/agents/requirements_agent/outputs/Roleplay_Simulation_Input_Packet.json" --output-dir "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs/local_prd_001" --llm-mode stub --write-outputs
```

### 생성 output

| output 파일 | 설명 |
|---|---|
| `Sanitized_Profile_Snapshot.json` | 개인정보 제거 후 agent 입력 |
| `Agent_Cards.json` | Role Agent 카드 |
| `Simulation_Phase_Plan.json` | phase/event 계획 |
| `Orchestrator_Output.json` | role turn 실행 결과 |
| `Team_Simulation_Log.json` | simulation log |
| `Issue_Risk_Summary.json` | issue/risk summary |
| `Score_Breakdown.json` | score breakdown |
| `Simulation_OUTPUT.json` | 최종 output |

### 완료 기준

- CLI 한 줄로 `Simulation_OUTPUT.json`까지 생성된다.
- summary에 phase/event/issue/verdict가 출력된다.

## Phase 8. End-to-End 검증 강화

### 목표

PRD부터 최종 RolePlay output까지 실제 로컬 MVP 흐름을 테스트로 고정한다.

### 테스트 범위

| 테스트 | 확인 내용 |
|---|---|
| feature preprocessing unit test | feature matrix schema, missing policy, normalization |
| requirements-employee compare test | requirements와 employee feature matrix 비교 결과 |
| employee ranking test | compare result 기반 직원 ranking |
| team composition/ranking test | employee ranking 기반 팀 후보와 팀 ranking |
| requirements local runner test | feature/compare/ranking/team outputs 포함 |
| roleplay local runner test | input packet -> `Simulation_OUTPUT.json` |
| full e2e test | PRD -> requirements -> preprocessing -> compare -> ranking -> roleplay output |

### 완료 기준

- `compileall` 통과
- `ruff check` 통과
- `pytest backend/tests -q` 통과
- 실제 PRD stub 실행 통과

## 7. 최종 실행 명령어 목표

### 1. Requirements + Preprocessing + Compare + Ranking 실행

```powershell
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" --employee-data-dir "datasets/raw" --llm-mode stub --write-outputs
```

### 2. Human Confirm 포함 실행

```powershell
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" --employee-data-dir "datasets/raw" --llm-mode stub --human-confirm-decision "backend/agents/requirements_agent/local_inputs/human_confirm_decision_prd_001.json" --write-outputs
```

### 3. RolePlay 최종 output 실행

```powershell
.venv\Scripts\python.exe -m backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.run_shadow_roleplay_local --input-packet "backend/agents/requirements_agent/outputs/Roleplay_Simulation_Input_Packet.json" --output-dir "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs/local_prd_001" --llm-mode stub --write-outputs
```

## 8. 최종 완료 기준

| 완료 조건 | 기준 |
|---|---|
| Feature Engineering 분리 | `Employee_Feature_Matrix.json`과 metadata 생성 |
| Compare 단계 분리 | `Requirements_Employee_Compare.json` 생성 |
| Employee Ranking 분리 | compare result 기반 `Employee_Fit_Ranking.json` 생성 |
| Team Composition/Ranking 분리 | team candidates와 team ranking 산출물 생성 |
| Evidence trace 유지 | feature -> compare -> ranking -> risk/score까지 추적 가능 |
| Human Confirm 적용 가능 | decision JSON 반영 후 final output 상태 변화 확인 |
| RolePlay CLI 사용 가능 | 한 줄 명령어로 `Simulation_OUTPUT.json` 생성 |
| Full local MVP 검증 | PRD에서 최종 RolePlay output까지 재현 가능 |
| 품질 검증 | compile/lint/test 전체 통과 |

## 9. 주의사항

- Feature engineering은 직원 개인 평가가 아니라 프로젝트 요구사항과 비교하기 위한 feature transformation이다.
- Compare는 ranking이 아니라 requirements와 employee feature의 충족/미충족/부분충족을 계산하는 중간 단계다.
- Ranking은 compare 결과를 기반으로 순위를 매기는 후속 단계다.
- Team ranking은 개인 점수 평균만 사용하지 않고 role coverage, skill coverage, risk, availability를 함께 본다.
- restricted/sensitive column은 preprocessing 단계에서 제거하거나 confirm 전까지 blocked 처리한다.
- raw DB value를 RolePlay Agent에 직접 넘기지 않는다.
- Human Confirm은 전역 taxonomy/rulebase를 자동 수정하지 않는다.
- RolePlay output verdict는 팀 조합의 프로젝트 적합도 판단이지 개인 인사 평가가 아니다.
