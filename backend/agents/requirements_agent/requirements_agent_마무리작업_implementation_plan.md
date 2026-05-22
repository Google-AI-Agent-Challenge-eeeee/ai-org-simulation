# Requirements Agent 마무리 작업 Implementation Plan

## 1. 문서 목적

이 문서는 `Final_Requirements_Agent_implementation_plan.md` 기반 Phase 0~10 구현이 완료된 뒤, Requirements Agent를 로컬에서 최종 검증하고 마무리하기 위한 작업 계획서다.

이번 마무리 작업의 목표는 Server, Cloud DB, 배포 연동이 아니다.

목표는 현재 workspace 안의 실제 input을 사용해서 Requirements Agent가 로컬에서 끝까지 실행되고, 최종 산출물인 `Requirements_List.json`을 문제 없이 생성할 수 있는지 확인하는 것이다.

## 2. 현재 전제

기준 workspace:

```text
C:\Users\happy\Documents\Codex\2026-05-21\ai-org-simulation
```

Requirements Agent 구현 위치:

```text
backend/agents/requirements_agent/
```

기준 구현 계획서:

```text
backend/agents/requirements_agent_민성초기세팅/Final_Requirements_Agent_implementation_plan.md
```

로컬 통합 계획서:

```text
backend/agents/requirements_agent/통합단계_작업_implementation_plan.md
```

실제 PRD input:

```text
backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf
```

실제 로컬 DB input:

```text
datasets/raw/hr/employee_dummy_100.csv
datasets/raw/github/github_activity_dummy_100.csv
datasets/raw/slack/slack_activity_dummy_100.csv
datasets/raw/jira/jira_activity_dummy_100.csv
datasets/raw/calendar/google_calendar_activity_dummy_100.csv
```

## 3. 이번 마무리 작업에서 하지 않는 것

아래 작업은 이번 마무리 범위에서 제외한다.

- Server API 연결
- Cloud DB 연결
- 배포 환경 구성
- 운영 DB 저장
- 프론트엔드 화면 연결
- 로그인/권한 처리
- 직원 적합도 점수 계산
- 팀 조합 추천
- Shadow RolePlay 실행

이번 단계는 Requirements Agent 자체가 로컬 input으로 최종 output을 만들 수 있는지 확인하는 단계다.

## 4. 최종 마무리 원칙

### 4.1 PRD 원문 보존

PRD 본문은 요약하거나 재작성하지 않는다.

PDF에서 추출한 원문은 `raw_text`, `raw_text_ref`, `section_id`, `chunk_id`, `source_evidence`를 통해 추적 가능해야 한다.

### 4.2 실제 DB column 기준 유지

column selection과 weighting은 `datasets/raw` 아래의 실제 CSV column을 기준으로 검증한다.

`employee_column_rules.json`에서 참조하는 column이 실제 CSV header에 없으면 마무리 완료로 보지 않는다.

### 4.3 taxonomy 자동 수정 금지

taxonomy에 없는 요구사항은 `unknown_requirements`로 분리한다.

Human Confirm 이후에도 전역 `taxonomy.json`은 자동 수정하지 않는다.

필요한 경우 이번 프로젝트 전용 `project_specific_mapping`으로만 처리한다.

### 4.4 outputs는 의도적으로 생성

일반 테스트에서는 outputs를 자동 생성하지 않는다.

하지만 이번 마무리 작업에서는 실제 동작 확인이 목적이므로 명시 옵션으로 `outputs/*.json`을 생성한다.

### 4.5 Human Confirm 항목 자동 삭제 금지

다음 항목은 자동 삭제하지 않는다.

- `unknown_requirements`
- `missing_extractions`
- `invalid_items`
- `low_confidence_items`
- `missing_fields`
- conflict candidates

위 항목은 Human Confirm 단계에서 사용자 판단으로 처리한다.

## 5. 최종 산출물 목록

마무리 작업에서 실제 생성 및 확인할 산출물은 다음과 같다.

```text
backend/agents/requirements_agent/outputs/Cleaned_PRD_Text.json
backend/agents/requirements_agent/outputs/Section_Extraction_Result.json
backend/agents/requirements_agent/outputs/Extracted_Requirements_Draft.json
backend/agents/requirements_agent/outputs/Mapped_Requirements.json
backend/agents/requirements_agent/outputs/Column_Selection_Draft.json
backend/agents/requirements_agent/outputs/Validation_Result.json
backend/agents/requirements_agent/outputs/Coverage_Check_Result.json
backend/agents/requirements_agent/outputs/Human_Confirm_Result.json
backend/agents/requirements_agent/outputs/Column_Weighting_Result.json
backend/agents/requirements_agent/outputs/Requirements_List.json
```

최종 핵심 산출물:

```text
backend/agents/requirements_agent/outputs/Requirements_List.json
```

## 6. 마무리 Phase 구성

## Finish Phase 0. 현재 상태 최종 점검

### 목표

Phase 0~10 구현물이 현재 workspace에서 정상 상태인지 확인한다.

### 작업 내용

- 현재 브랜치 확인
- `backend/agents/requirements_agent/` 파일 구조 확인
- `outputs/` 현재 상태 확인
- `datasets/raw` CSV 존재 여부 확인
- `PRD_001_notification_center.pdf` 존재 여부 확인
- Requirements Agent 관련 테스트 현황 확인
- `employee_column_rules.json`의 참조 column이 실제 CSV header에 모두 존재하는지 확인

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 0 작업을 진행해줘.
현재 workspace 기준으로 requirements_agent 구현 상태, outputs 상태,
PRD_001_notification_center.pdf 존재 여부, datasets/raw CSV 존재 여부를 확인하고,
employee_column_rules.json이 실제 CSV header와 충돌하지 않는지도 검증해줘.
아직 파일 수정이나 outputs 생성은 하지 말고 결과만 정리해줘.
```

### 완료 기준

- 실제 PRD input 확인 완료
- 실제 DB input 확인 완료
- reference column과 실제 CSV column 충돌 없음
- 다음 phase에서 local loader/runner 마무리 가능

## Finish Phase 1. PRD PDF Local Input 처리 마무리

### 목표

`PRD_001_notification_center.pdf`를 Requirements Agent pipeline 입력으로 사용할 수 있게 한다.

### 생성 또는 수정 후보 파일

```text
backend/agents/requirements_agent/pipeline/local_input_loader.py
backend/tests/test_requirements_agent_local_input_loader.py
```

### 작업 내용

- PDF에서 텍스트 추출 가능 여부 확인
- 텍스트 PDF면 직접 text extraction 처리
- 이미지 PDF면 OCR 필요 여부를 명확히 표시
- 추출한 PRD 본문을 요약 없이 `raw_text`로 보존
- `document_id`는 예시로 `prd_001_notification_center` 사용
- `raw_text_ref`는 원본 PDF 경로 기반으로 생성
- section splitter에 넘길 수 있는 형태로 반환

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 1 작업을 진행해줘.
PRD_001_notification_center.pdf를 로컬 input으로 읽을 수 있게 처리해줘.
PDF 본문은 요약하지 말고 raw_text로 보존하고,
텍스트 추출 가능 여부와 OCR 필요 여부를 확인해줘.
필요하면 local_input_loader.py와 테스트를 추가해줘.
```

### 완료 기준

- PDF에서 PRD raw text 확보
- PRD 원문 보존 확인
- section splitter 입력 가능
- loader 테스트 통과

## Finish Phase 2. datasets/raw DB Column Loader 마무리

### 목표

`datasets/raw` 아래 CSV column을 읽어 Requirements Agent의 column selection 검증 기준으로 사용한다.

### 생성 또는 수정 후보 파일

```text
backend/agents/requirements_agent/pipeline/local_input_loader.py
backend/tests/test_requirements_agent_local_input_loader.py
```

### 작업 내용

- HR, GitHub, Slack, Jira, Calendar CSV header 읽기
- source별 column map 생성
- `employee_column_rules.json`의 `column_sources`와 비교
- `requirement_type_rules`에서 참조하는 모든 column이 실제 CSV header에 있는지 검증
- restricted/excluded/not_available column 정책을 유지
- 실제 개인 row data는 scoring 단계가 아니므로 읽지 않거나 최소한으로 다룸

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 2 작업을 진행해줘.
datasets/raw 아래 HR, GitHub, Slack, Jira, Calendar CSV header를 읽어
employee_column_rules.json과 비교하는 로컬 DB column loader를 마무리해줘.
실제 직원 개인 평가가 아니라 column 기준 검증만 수행하고,
참조 column 누락이 있으면 명확히 보고하게 해줘.
```

### 완료 기준

- source별 실제 CSV column map 생성 가능
- `employee_column_rules.json` 참조 column 검증 가능
- 실제 CSV header와 충돌 없음
- 테스트 통과

## Finish Phase 3. Local Runner 마무리

### 목표

PRD PDF와 `datasets/raw`를 입력으로 받아 Phase 1~10 pipeline을 한 번에 실행하는 local runner를 만든다.

### 생성 또는 수정 후보 파일

```text
backend/agents/requirements_agent/pipeline/run_requirements_agent_local.py
backend/tests/test_requirements_agent_local_runner.py
```

### 목표 명령 형태

```powershell
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local `
  --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" `
  --employee-data-dir "datasets/raw" `
  --write-outputs
```

### 작업 내용

- local input loader와 기존 `requirements_pipeline.py` 연결
- `--prd` 옵션 지원
- `--employee-data-dir` 옵션 지원
- `--write-outputs` 옵션 지원
- 실행 summary 출력
- phase별 성공/실패 상태 출력
- schema validation 결과 출력
- 실패 시 어느 단계에서 실패했는지 알 수 있게 error report 구성

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 3 작업을 진행해줘.
PRD_001_notification_center.pdf와 datasets/raw를 입력으로 받아
기존 Phase 1~10 pipeline을 실행하는 local runner를 구현해줘.
--write-outputs 옵션이 있을 때만 outputs/*.json을 생성하고,
실행 summary와 schema validation 결과를 출력하게 해줘.
작업 후 local runner 테스트까지 추가해줘.
```

### 완료 기준

- local runner 명령 실행 가능
- 실제 PRD PDF 입력 가능
- 실제 `datasets/raw` 기준 column 검증 가능
- `--write-outputs` 옵션으로 outputs 생성 가능
- runner 테스트 통과

## Finish Phase 4. 실제 PRD 기반 outputs 최초 생성

### 목표

`PRD_001_notification_center.pdf`와 `datasets/raw`를 사용해 실제 output JSON을 생성한다.

### 작업 내용

- outputs 폴더 현재 상태 기록
- local runner 실행
- 10개 output JSON 생성 확인
- 각 output JSON이 비어 있지 않은지 확인
- `Requirements_List.json` 생성 확인
- schema validation 통과 여부 확인
- source evidence가 PRD section/chunk를 가리키는지 확인
- selected employee columns가 실제 CSV column 기준과 충돌하지 않는지 확인

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 4 작업을 진행해줘.
PRD_001_notification_center.pdf와 datasets/raw를 사용해서 local runner를 실제 실행하고,
outputs/*.json 산출물을 생성해줘.
생성된 10개 output 파일의 존재 여부, 비어 있지 않은지,
Requirements_List.json schema validation 결과,
source evidence 추적 가능 여부,
selected employee columns와 실제 CSV column 충돌 여부를 정리해줘.
```

### 완료 기준

- 10개 output JSON 생성 완료
- `Requirements_List.json` 생성 완료
- 최종 schema validation 통과
- source evidence 추적 가능
- selected column이 실제 CSV header와 충돌하지 않음

## Finish Phase 5. Output 품질 검토

### 목표

생성된 outputs가 Requirements Agent 목적에 맞는 품질인지 확인한다.

### 검토 대상

```text
Cleaned_PRD_Text.json
Section_Extraction_Result.json
Extracted_Requirements_Draft.json
Mapped_Requirements.json
Column_Selection_Draft.json
Validation_Result.json
Coverage_Check_Result.json
Human_Confirm_Result.json
Column_Weighting_Result.json
Requirements_List.json
```

### 작업 내용

- PRD section이 누락 없이 반영됐는지 확인
- raw requirement 후보가 source evidence를 가지는지 확인
- taxonomy mapping이 억지 매핑을 하지 않았는지 확인
- `unknown_requirements`가 적절히 분리됐는지 확인
- missing/invalid/low confidence 항목이 Human Confirm 대상으로 남았는지 확인
- coverage status가 section map 기준으로 계산됐는지 확인
- column selection이 직원 개인 점수가 아니라 비교 기준으로 구성됐는지 확인
- column weights 합계와 priority order가 타당한지 확인

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 5 작업을 진행해줘.
Phase 4에서 생성된 outputs/*.json을 기준으로 output 품질을 검토해줘.
PRD section 반영, source evidence, taxonomy mapping, unknown 분리,
validation, coverage, column selection, column weighting, 최종 Requirements_List 구조를 확인하고
문제가 있으면 어떤 파일/모듈을 수정해야 하는지 정리해줘.
```

### 완료 기준

- output별 품질 검토 완료
- 수정 필요 항목 정리
- Human Confirm 필요 항목 정리
- 후속 수정 없이 완료 가능한지 판단 가능

## Finish Phase 6. Human Confirm 로컬 반영

### 목표

실제 output에서 확인이 필요한 항목을 사용자 결정 기준으로 반영하고 최종 산출물을 다시 생성한다.

### 생성 후보 파일

```text
backend/agents/requirements_agent/local_inputs/human_confirm_decision_prd_001.json
```

또는 outputs에 직접 생성되는 결과:

```text
backend/agents/requirements_agent/outputs/Human_Confirm_Result.json
```

### 작업 내용

- `unknown_requirements` 확인
- `missing_extractions` 확인
- `invalid_items` 확인
- `low_confidence_items` 확인
- `missing_fields` 확인
- `project_specific_mapping` 작성
- `removed_items` 작성
- restricted column 사용 여부 확인
- Human Confirm 반영 후 final builder 재실행
- 전역 `taxonomy.json`, `rulebase.json` 자동 수정 없음 확인

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 6 작업을 진행해줘.
Phase 5에서 확인된 unknown/missing/invalid/low confidence/missing fields를 기준으로
로컬 Human Confirm decision을 반영해줘.
전역 taxonomy.json은 수정하지 말고 project_specific_mapping과 removed_items만 사용해
최종 Requirements_List.json을 다시 생성하고 schema validation까지 확인해줘.
```

### 완료 기준

- Human Confirm decision 반영 완료
- 전역 reference 파일 자동 변경 없음
- 최종 `Requirements_List.json` 재생성 완료
- schema validation 통과

## Finish Phase 7. Regression Test 및 반복 실행 검증

### 목표

마무리 작업 후 기존 구현이 깨지지 않았고, 실제 local runner 실행이 반복 가능한지 확인한다.

### 검증 명령

Requirements Agent 전용 테스트:

```powershell
.venv\Scripts\pytest.exe backend/tests/test_requirements_agent_*.py
```

backend 전체 테스트:

```powershell
.venv\Scripts\pytest.exe backend/tests
```

local runner 재실행:

```powershell
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local `
  --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" `
  --employee-data-dir "datasets/raw" `
  --write-outputs
```

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 7 작업을 진행해줘.
Requirements Agent 전용 테스트, backend 전체 테스트, local runner 반복 실행을 수행하고,
테스트 결과와 outputs 재생성 결과를 정리해줘.
실패가 있으면 수정하고, 최종적으로 Requirements Agent 로컬 구현 완료 여부를 판단해줘.
```

### 완료 기준

- Requirements Agent 전용 테스트 통과
- backend 전체 테스트 통과
- local runner 반복 실행 가능
- outputs 재생성 가능
- 최종 산출물 schema validation 통과

## Finish Phase 8. 최종 마무리 보고

### 목표

Requirements Agent가 로컬 구현 완료 상태인지 최종 정리한다.

### 정리 항목

- 사용한 PRD input
- 사용한 DB input
- 생성된 outputs 목록
- 최종 `Requirements_List.json` validation 결과
- unknown/missing/invalid/low confidence 상태
- Human Confirm 반영 여부
- selected employee columns 검증 결과
- 테스트 결과
- 남은 위험 또는 후속 작업

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 Phase 8 작업을 진행해줘.
Phase 0~7까지의 결과를 기준으로 최종 마무리 보고를 작성해줘.
사용한 PRD/DB input, 생성된 outputs, Requirements_List schema validation,
Human Confirm 반영 여부, 테스트 결과, 남은 위험, 다음 단계로 넘어가도 되는지를 정리해줘.
```

### 완료 기준

- 로컬 Requirements Agent 구현 완료 여부 명확화
- 후속 단계로 넘길 수 있는 산출물 확인
- 남은 작업이 있으면 범위와 우선순위 정리

## 7. 추천 실행 순서

| 순서 | Phase | 작업 | 핵심 산출 |
|---:|---|---|---|
| 1 | Finish Phase 0 | 현재 상태 최종 점검 | input/reference 상태 보고 |
| 2 | Finish Phase 1 | PRD PDF input 처리 | PRD raw text loader |
| 3 | Finish Phase 2 | datasets/raw column 처리 | DB column map |
| 4 | Finish Phase 3 | local runner 구현 | local runner |
| 5 | Finish Phase 4 | 실제 outputs 생성 | `outputs/*.json` |
| 6 | Finish Phase 5 | output 품질 검토 | 수정/Human Confirm 항목 |
| 7 | Finish Phase 6 | Human Confirm 반영 | 최종 `Requirements_List.json` |
| 8 | Finish Phase 7 | 테스트 및 반복 실행 | 테스트 결과 |
| 9 | Finish Phase 8 | 최종 보고 | 완료 판단 |

## 8. 최종 완료 기준

Requirements Agent 마무리 작업 완료 기준은 다음과 같다.

- `PRD_001_notification_center.pdf`를 실제 input으로 사용했다.
- `datasets/raw`의 실제 CSV column을 기준으로 column selection을 검증했다.
- PRD raw text가 요약 없이 보존됐다.
- source evidence가 final output까지 추적 가능하다.
- taxonomy에 없는 항목이 자동 추가되지 않았다.
- Human Confirm 대상이 자동 삭제되지 않았다.
- `outputs/*.json` 10개가 명시 실행으로 생성됐다.
- `Requirements_List.json`이 schema validation을 통과했다.
- selected employee columns가 실제 CSV header와 충돌하지 않는다.
- Requirements Agent 전용 테스트가 통과했다.
- backend 전체 테스트가 통과했다.
- local runner를 반복 실행할 수 있다.
- Server/Cloud DB 없이 로컬 구현 완료 상태라고 판단할 수 있다.

## 9. 주의사항

- 이 문서는 최종 마무리 작업 계획서이며, 인프라 연동 계획서가 아니다.
- outputs 생성 전 기존 outputs 상태를 먼저 확인한다.
- output 파일을 지우거나 덮어쓸 때는 의도된 마무리 실행인지 확인한다.
- PDF가 이미지 기반이면 OCR 필요 여부를 먼저 보고한다.
- 실제 직원 row data는 이번 단계에서 평가 대상이 아니다.
- column weight는 직원 개인 점수가 아니라 프로젝트 요구사항과 직원 DB 비교 기준이다.
- Human Confirm 결과로 전역 taxonomy/rulebase/reference를 자동 수정하지 않는다.
- unknown requirement가 남아 있으면 후속 직원 적합도 계산으로 바로 넘기지 않는다.

