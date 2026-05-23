# Requirements RolePlay Matching 중간점검 체크리스트

## 1. 문서 목적

이 문서는 `requirements_agent -> ranking/team module -> roleplay_agent` 흐름의 중간점검을 위한 체크리스트다. 구현 중간과 최종 검토 시, 각 산출물이 다음 단계에 필요한 정보를 충분히 전달하는지 확인한다.

## 2. 점검 기준 요약

| 구분 | 점검 목표 | 상태 | 메모 |
|---|---|---|---|
| 1. Requirements Agent | PRD에서 role/skill/risk/column 기준을 안정적으로 생성하는가 | TODO |  |
| 2. Ranking/Team Module | 프로젝트에 필요한 후보와 팀 조합만 생성하는가 | TODO |  |
| 3. RolePlay Agent | 입력 packet으로 실제 simulation output을 생성하는가 | TODO |  |
| 4. Agent 간 흐름 | 산출물이 정보 손실 없이 다음 단계로 전달되는가 | TODO |  |

## 3. Requirements Agent 점검

### 1-1. Requirements Agent Input

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| PRD 파일이 존재하는가 | `PRD_001_notification_center.pdf` 또는 사용자 지정 PRD 경로 확인 | TODO |  |
| PRD 원문이 축약 없이 로드되는가 | `raw_text_ref`, `raw_text_length`, `source_uri` 보존 | TODO |  |
| `datasets/raw` 직원 DB가 존재하는가 | HR/GitHub/Slack/Jira/Calendar CSV 확인 | TODO |  |
| reference 파일이 존재하는가 | `taxonomy.json`, `rulebase.json`, `employee_column_rules.json` | TODO |  |
| schema 파일이 존재하는가 | `requirements_schema.json`, draft/mapped schema | TODO |  |
| LLM mode가 명확한가 | `stub`, `gemini_api`, `vertex` 중 하나 | TODO |  |
| Human Confirm decision 입력이 있으면 로드되는가 | project specific mapping, removed items 반영 | TODO |  |

### 1-2. Requirements Agent Output

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| `Cleaned_PRD_Text.json` 생성 | raw text, section map, token status 포함 | TODO |  |
| `Section_Extraction_Result.json` 생성 | section별 후보와 source evidence 포함 | TODO |  |
| `Extracted_Requirements_Draft.json` 생성 | chunk merge, duplicate/conflict 정보 포함 | TODO |  |
| `Mapped_Requirements.json` 생성 | taxonomy matched items와 `unknown_requirements` 분리 | TODO |  |
| `Column_Selection_Draft.json` 생성 | 후보 column과 선택 이유 포함 | TODO |  |
| `Validation_Result.json` 생성 | missing/invalid/low confidence 분리 | TODO |  |
| `Coverage_Check_Result.json` 생성 | section별 covered/partial/missing 계산 | TODO |  |
| `Human_Confirm_Result.json` 생성 | 확인 필요 항목과 project mapping 포함 | TODO |  |
| `Column_Weighting_Result.json` 생성 | column weights, priority, reason 포함 | TODO |  |
| `Requirements_List.json` 생성 | schema validation 통과 | TODO |  |
| `Roleplay_Requirements_Input.json` 생성 | RolePlay `RequirementsList` schema 호환 | TODO |  |
| `Roleplay_Handoff_Manifest.json` 생성 | 제공 input과 review count 명시 | TODO |  |

### 1-3. Requirements Agent 완성도

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| taxonomy 자동 수정 금지 | unknown은 전역 taxonomy에 자동 반영하지 않음 | TODO |  |
| source evidence 필수 원칙 | 주요 requirement에 evidence 연결 | TODO |  |
| unknown/missing/low confidence 분리 | 삭제하지 않고 Human Confirm 대상으로 유지 | TODO |  |
| required roles 품질 | 너무 넓거나 누락된 role이 없는지 확인 | TODO |  |
| required skills 품질 | RolePlay와 ranking에 필요한 skill 표현인지 확인 | TODO |  |
| risk factors 품질 | RolePlay issue category로 매핑 가능한지 확인 | TODO |  |
| selected columns 품질 | 직원 비교에 필요한 column만 포함 | TODO |  |
| column weights 품질 | 프로젝트 요구사항 기준이며 개인 평가 점수가 아님 | TODO |  |

## 4. Ranking/Team Module 점검

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| 직원 DB join 정상 | HR 기준으로 GitHub/Slack/Jira/Calendar 연결 | TODO |  |
| BOM/인코딩 처리 | `employee_id`가 빈 값으로 읽히지 않음 | TODO |  |
| 후보 범위 제한 | PRD required role에 해당하는 직원만 ranking 후보 | TODO |  |
| PM proxy 정책 | PM 전용 직군이 없으면 leadership/ownership 기반 후보 제한 | TODO |  |
| role별 후보 수 | `role_candidate_counts`로 확인 가능 | TODO |  |
| shortlisted candidates | role별 top N 확인 가능 | TODO |  |
| 사용 column 명시 | `used_employee_columns`에 scoring/evidence column 기록 | TODO |  |
| employee fit score | role match, project weighted fit, delivery, availability, communication 반영 | TODO |  |
| team composition | ranking 후보군 안에서만 조합 생성 | TODO |  |
| 중복 직원 방지 | 한 팀에 같은 employee_id 중복 없음 | TODO |  |
| required role coverage | covered/uncovered role 확인 가능 | TODO |  |
| uncovered role penalty | 미커버 role이 team score에 반영 | TODO |  |
| team risk summary | 팀 단위 risk tags, prior scores, bottleneck, dependencies 포함 | TODO |  |
| evidence metadata | risk tag별 evidence 최소 1개 이상 또는 gap 명시 | TODO |  |
| RolePlay packet 생성 | `Roleplay_Simulation_Input_Packet.json` schema validation 통과 | TODO |  |

## 5. RolePlay Agent 점검

### 3-1. RolePlay Agent Input

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| `RequirementsList` 입력 가능 | `Roleplay_Requirements_Input.json` Pydantic validation 통과 | TODO |  |
| `SelectedTeamRecord` 입력 가능 | 선택 팀 2명 이상, 역할 배치 포함 | TODO |  |
| `EmployeeFitProfileSnapshot` 입력 가능 | 팀원별 signals, matched/missing skills 포함 | TODO |  |
| `TeamRiskSummary` 입력 가능 | risk tags와 prior scores 포함 | TODO |  |
| `EvidenceMetadata` 입력 가능 | risk/source_column/signal_value/interpretation 포함 | TODO |  |
| `SimulationInputPacket` 생성 | 5개 input이 하나로 병합됨 | TODO |  |
| 원천 DB 직접 사용 없음 | RolePlay가 raw Git/Jira/Slack/Calendar DB를 직접 읽지 않음 | TODO |  |

### 3-2. RolePlay Agent Output

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| `Sanitized_Profile_Snapshot.json` 생성 | 개인정보/원천 detail 제거, signal만 유지 | TODO |  |
| `Agent_Cards.json` 생성 | 역할, 책임, 제약, risk, evidence refs 포함 | TODO |  |
| `Simulation_Phase_Plan.json` 생성 | 5개 phase와 scenario events 포함 | TODO |  |
| `Orchestrator_Output.json` 생성 | phase event별 Role Agent turns 포함 | TODO |  |
| `Team_Simulation_Log.json` 생성 | structured log, issues, actions, phase scores 포함 | TODO |  |
| `Issue_Risk_Summary.json` 생성 | confirmed/candidate/invalid issues 분리 | TODO |  |
| `Score_Breakdown.json` 생성 | 7개 dimension score와 overall fit 포함 | TODO |  |
| `Simulation_OUTPUT.json` 생성 | verdict, top risks, must-fix actions 포함 | TODO |  |

### 3-3. RolePlay Agent 완성도

| 체크 항목 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|
| scenario event 수 | 최소 1개 이상, risk 기반 생성 | TODO |  |
| Role Agent turn 수 | 최소 1개 이상, structured fields 포함 | TODO |  |
| evidence 기반 발언 | concern은 evidence 또는 risk trigger에 연결 | TODO |  |
| issue 확정 기준 | prior risk + observed simulation risk 결합 | TODO |  |
| 빈 simulation 방지 | event/turn/log가 0이면 성공으로 처리하지 않음 | TODO |  |
| verdict 표현 | 개인 평가가 아니라 프로젝트 조건에서의 팀 안정성으로 표현 | TODO |  |
| lint 상태 | Shadow RolePlay module lint 통과 | TODO |  |
| test coverage | RolePlay e2e/unit 테스트 존재 | TODO |  |

## 6. Requirements Agent와 RolePlay Agent 간 흐름 점검

### 4-1. 산출물 전달 품질

| 전달 구간 | 전달 파일/값 | 기대 상태 | 점검 결과 | 문제/개선 |
|---|---|---|---|---|
| Requirements -> Ranking | `required_roles` | 후보 직군 필터링 기준으로 사용 | TODO |  |
| Requirements -> Ranking | `required_skills` | skill match score에 사용 | TODO |  |
| Requirements -> Ranking | `selected_employee_columns` | 직원 DB 비교 기준으로 사용 | TODO |  |
| Requirements -> Ranking | `column_weights` | project weighted fit 계산에 사용 | TODO |  |
| Requirements -> Ranking | `risk_factors` | team risk summary 생성에 사용 | TODO |  |
| Ranking -> RolePlay | `Roleplay_Selected_Team_Record` | simulation 대상 팀 정의 | TODO |  |
| Ranking -> RolePlay | `Roleplay_Employee_Fit_Profile_Snapshots` | Agent Card 생성 기준 | TODO |  |
| Ranking -> RolePlay | `Roleplay_Team_Risk_Summary` | scenario event, issue prior 기준 | TODO |  |
| Ranking -> RolePlay | `Roleplay_Evidence_Metadata` | Role Agent concern, evaluator evidence 기준 | TODO |  |
| Ranking -> RolePlay | `Roleplay_Simulation_Input_Packet` | RolePlay 전체 실행 input | TODO |  |
| RolePlay -> Final | `Team_Simulation_Log` | observed risk source | TODO |  |
| RolePlay -> Final | `Issue_Risk_Summary` | score/verdict 계산 기준 | TODO |  |
| RolePlay -> Final | `Simulation_OUTPUT` | 최종 판단 산출물 | TODO |  |

### 4-2. 흐름 문제점 및 개선사항

| 문제 ID | 발생 구간 | 문제 | 영향 | 개선 작업 | 상태 |
|---|---|---|---|---|---|
| F1 | Requirements/Risk -> RolePlay Planner | risk tag vocabulary 불일치 | scenario event 미생성 | risk bridge mapping 추가 | TODO |
| F2 | RolePlay Planner | template 없는 risk fallback 없음 | simulation turn 0개 | generic fallback event builder 추가 | TODO |
| F3 | Ranking -> Evidence | 일부 risk에 evidence 없음 | issue 확정 근거 부족 | evidence fallback 생성 | TODO |
| F4 | Ranking -> Team | selected team required role 미커버 | 역할 관점 simulation 누락 | coverage gap 명시 및 penalty | TODO |
| F5 | Requirements -> Ranking | required role이 넓으면 후보 과다 | shortlist 가독성 저하 | must/should/support role 분리 | TODO |
| F6 | RolePlay -> Final | event/turn/log 0이어도 output 생성 | 잘못된 proceed verdict 가능 | empty simulation guard 추가 | TODO |
| F7 | Quality | RolePlay lint 미정리 | CI 품질 리스크 | lint 정리 | TODO |
| F8 | Quality | RolePlay e2e 테스트 부족 | 회귀 탐지 어려움 | e2e/unit 테스트 추가 | TODO |

## 7. 중간점검 실행 명령

```powershell
.venv\Scripts\python.exe -m compileall -q backend\agents
.venv\Scripts\python.exe -m ruff check backend\agents backend\tests\test_requirements_agent_*.py
.venv\Scripts\python.exe -m pytest backend\tests -q
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" --employee-data-dir "datasets/raw" --llm-mode stub --write-outputs
```

## 8. 완료 판정

| 완료 조건 | 판정 |
|---|---|
| Requirements Agent 산출물이 모두 schema validation을 통과한다 | TODO |
| ranking/team module이 PRD role 기반 후보와 팀 조합을 생성한다 | TODO |
| RolePlay input 5종이 모두 생성되고 schema validation을 통과한다 | TODO |
| Scenario planner가 최소 1개 이상의 event를 생성한다 | TODO |
| Orchestrator가 최소 1개 이상의 Role Agent turn을 생성한다 | TODO |
| Issue/Risk Evaluator가 evidence/log 기반 summary를 생성한다 | TODO |
| Simulation output이 빈 simulation 기준 verdict가 아니다 | TODO |
| 전체 tests와 lint가 통과한다 | TODO |
## 9. 2026-05-23 실행 점검 결과

| 점검 항목 | 결과 | 메모 |
|---|---:|---|
| Requirements Agent 로컬 stub 실행 | PASS | `written_file_count=19`, `Roleplay_Simulation_Input_Packet.json` 생성 |
| PRD -> requirements outputs | PASS | `Requirements_List.json` 포함 기존 10개 산출물 생성 |
| requirements -> ranking/team module | PASS | `employee_fit_candidate_count=88`, `team_candidate_count=20`, `selected_team_id=team_001` |
| ranking -> RolePlay input 5종 | PASS | selected team, snapshots, risk summary, evidence metadata, simulation packet 생성 |
| RolePlay planner event 생성 | PASS | 실제 outputs 기준 `scenario_event_count=17` |
| RolePlay orchestrator turn 생성 | PASS | 실제 outputs 기준 `orchestrator_phase_run_count=17` |
| Team simulation log 생성 | PASS | 실제 outputs 기준 `team_simulation_phase_log_count=5` |
| Issue/Risk summary 생성 | PASS | 실제 outputs 기준 confirmed 2건, candidate 4건 |
| Simulation output 생성 | PASS | `overall_project_fit=0.7746`, `verdict=proceed_with_conditions` |
| compile/lint/test | PASS | `compileall`, `ruff check`, `pytest backend/tests -q` 통과 |

### 확인된 이슈 및 처리

| 이슈 | 처리 |
|---|---|
| Requirements/ranking risk tag와 RolePlay scenario template tag가 달라 event가 0개가 될 수 있음 | `risk_taxonomy_bridge.py` 추가, canonical issue category 매핑 및 fallback routing 구현 |
| template이 없는 risk가 simulation에서 사라짐 | `ScenarioPhasePlanner`에 generic fallback event builder 추가 |
| 일부 team risk tag가 evidence 없이 전달될 수 있음 | `employee_team_ranking.py`에서 risk별 fallback evidence metadata 생성 |
| selected team이 모든 required role을 커버하지 못할 때 downstream에서 누락이 보이지 않음 | handoff manifest와 team risk summary에 role coverage gap 및 `unclear_ownership` risk 반영 |
| RolePlay lint 미정리 | ruff auto-fix 및 잔여 lint 수동 정리 완료 |

### 남은 주의사항

- 현재 로컬 PRD stub 결과는 `pipeline_status=needs_human_confirm`이다. unknown 2건, low confidence 5건이 남아 있어 실제 확정 run에서는 Human Confirm 입력 또는 project-specific mapping 검토가 필요하다.
- 이번 검증은 LLM API가 아닌 `stub` 기준이다. Vertex/Gemini 실사용 검증은 별도 API quota/권한이 안정화된 뒤 같은 pipeline으로 재실행하면 된다.
