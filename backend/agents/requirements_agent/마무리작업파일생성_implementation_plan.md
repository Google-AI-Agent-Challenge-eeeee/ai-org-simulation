# Requirements Agent 마무리 작업 파일 생성 Implementation Plan

## 1. 문서 목적

이 문서는 `requirements_agent_마무리작업_implementation_plan.md`를 실제로 수행하기 전에, 최종 마무리 작업에 필요한 폴더/파일/자료를 어떤 순서로 생성해야 하는지 정리한 파일 생성 계획서다.

이 문서는 Requirements Agent 기능 구현 계획서가 아니다.

목표는 최종 마무리 작업을 시작하기 전에 필요한 실행 보조 파일, local input 파일, LLM adapter 파일, local runner 파일, 테스트 파일을 정리하고 생성 순서를 확정하는 것이다.

## 2. 현재 이미 준비된 자료

아래 자료는 이미 작업 폴더에 있으므로 새로 생성하지 않는다.

### 2.1 PRD input

```text
backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf
```

### 2.2 로컬 DB input

```text
datasets/raw/hr/employee_dummy_100.csv
datasets/raw/github/github_activity_dummy_100.csv
datasets/raw/slack/slack_activity_dummy_100.csv
datasets/raw/jira/jira_activity_dummy_100.csv
datasets/raw/calendar/google_calendar_activity_dummy_100.csv
```

### 2.3 Requirements Agent reference

```text
backend/agents/requirements_agent/references/taxonomy.json
backend/agents/requirements_agent/references/rulebase.json
backend/agents/requirements_agent/references/employee_column_rules.json
```

### 2.4 Requirements Agent schema

```text
backend/agents/requirements_agent/schemas/requirements_schema.json
backend/agents/requirements_agent/schemas/extracted_requirements_draft_schema.json
backend/agents/requirements_agent/schemas/mapped_requirements_schema.json
```

### 2.5 Requirements Agent prompt

```text
backend/agents/requirements_agent/prompts/requirements_extractor_prompt.md
backend/agents/requirements_agent/prompts/validator_agent_prompt.md
backend/agents/requirements_agent/prompts/Column_Explain_Prompt.md
```

## 3. 새로 생성해야 하는 대상 요약

최종 마무리 작업을 위해 새로 생성해야 하는 핵심 대상은 다음과 같다.

| 구분 | 생성 대상 | 필수 여부 | 목적 |
|---|---|---:|---|
| local input 폴더 | `backend/agents/requirements_agent/local_inputs/` | 선택 | Human Confirm decision 등 로컬 실행 입력 보관 |
| PDF/CSV loader | `backend/agents/requirements_agent/pipeline/local_input_loader.py` | 필수 | PRD PDF와 `datasets/raw` CSV header를 pipeline input으로 변환 |
| LLM adapter | `backend/agents/requirements_agent/pipeline/llm_adapter.py` | 필수 | stub/vertex 등 LLM 호출 interface 정리 |
| Vertex extractor | `backend/agents/requirements_agent/pipeline/vertex_requirements_extractor.py` | 필수 | Vertex Gemini로 section requirement extraction 수행 |
| local runner | `backend/agents/requirements_agent/pipeline/run_requirements_agent_local.py` | 필수 | PRD + DB + LLM mode로 Phase 1~10 실행 |
| Human Confirm decision | `backend/agents/requirements_agent/local_inputs/human_confirm_decision_prd_001.json` | 조건부 | unknown/missing/invalid 항목이 있을 때 사용자 결정 반영 |
| loader test | `backend/tests/test_requirements_agent_local_input_loader.py` | 필수 | PDF/CSV input 처리 검증 |
| LLM adapter test | `backend/tests/test_requirements_agent_llm_adapter.py` | 필수 | LLM adapter contract 검증 |
| local runner test | `backend/tests/test_requirements_agent_local_runner.py` | 필수 | local runner 실행 흐름 검증 |
| output policy test | `backend/tests/test_requirements_agent_finish_outputs.py` | 권장 | 실제 outputs 생성 정책 검증 |

## 4. 생성하지 말아야 하는 대상

아래 파일은 손으로 미리 생성하지 않는다.

이 파일들은 local runner 실행 결과로 생성되어야 한다.

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

## 5. 파일 생성 Phase 구성

## File Create Phase 0. 생성 전 상태 확인

### 목표

필요 파일이 이미 있는지 확인하고, 중복 생성이나 잘못된 위치 생성을 방지한다.

### 확인 대상

```text
backend/agents/requirements_agent/pipeline/local_input_loader.py
backend/agents/requirements_agent/pipeline/llm_adapter.py
backend/agents/requirements_agent/pipeline/vertex_requirements_extractor.py
backend/agents/requirements_agent/pipeline/run_requirements_agent_local.py
backend/agents/requirements_agent/local_inputs/
backend/tests/test_requirements_agent_local_input_loader.py
backend/tests/test_requirements_agent_llm_adapter.py
backend/tests/test_requirements_agent_local_runner.py
backend/tests/test_requirements_agent_finish_outputs.py
```

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 0 작업을 진행해줘.
최종 마무리 작업에 필요한 local input loader, LLM adapter, vertex extractor,
local runner, 테스트 파일, local_inputs 폴더가 현재 존재하는지 확인하고,
없는 것만 생성 대상으로 정리해줘.
아직 파일 생성이나 수정은 하지 말고 결과만 알려줘.
```

### 완료 기준

- 현재 없는 파일 목록 확인
- 중복 생성 방지
- 생성 순서 확정 가능

## File Create Phase 1. local_inputs 폴더 생성

### 목표

로컬 실행에 필요한 Human Confirm decision 등 보조 input을 둘 폴더를 만든다.

### 생성 대상

```text
backend/agents/requirements_agent/local_inputs/
```

### 선택 생성 대상

```text
backend/agents/requirements_agent/local_inputs/.gitkeep
```

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 1 작업을 진행해줘.
backend/agents/requirements_agent/local_inputs/ 폴더를 생성해줘.
아직 Human Confirm decision 파일은 실제 output 검토 전이므로 만들지 말고,
필요하면 빈 폴더 유지를 위한 .gitkeep만 생성해줘.
```

### 완료 기준

- `local_inputs/` 폴더 존재
- Human Confirm decision 파일은 아직 생성하지 않음

## File Create Phase 2. Local Input Loader 파일 생성

### 목표

PRD PDF와 `datasets/raw` CSV header를 읽는 로컬 입력 파일을 생성한다.

### 생성 대상

```text
backend/agents/requirements_agent/pipeline/local_input_loader.py
backend/tests/test_requirements_agent_local_input_loader.py
```

### 포함해야 하는 기능

- PRD PDF 경로 검증
- PDF text extraction
- PDF가 이미지 기반일 경우 OCR 필요 상태 반환
- raw text 보존
- `document_id` 생성
- `source_uri`와 `raw_text_ref` 생성
- `datasets/raw` source별 CSV header 읽기
- `employee_column_rules.json` 참조 column과 실제 header 비교
- 개인 row data를 직원 평가 목적으로 사용하지 않음

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 2 작업을 진행해줘.
local_input_loader.py와 해당 테스트 파일을 생성해줘.
PRD_001_notification_center.pdf를 raw_text로 읽을 수 있게 하고,
datasets/raw의 HR, GitHub, Slack, Jira, Calendar CSV header를 읽어
employee_column_rules.json의 참조 column과 비교할 수 있게 해줘.
PDF 본문은 요약하지 말고 보존하고, 이미지 PDF라면 OCR 필요 상태를 명확히 반환하게 해줘.
```

### 완료 기준

- loader 파일 생성
- loader 테스트 생성
- PDF/CSV header 처리 contract 명확화

## File Create Phase 3. LLM Adapter 파일 생성

### 목표

Requirements Agent에서 실제 LLM API와 stub 실행을 같은 interface로 다룰 수 있게 한다.

### 생성 대상

```text
backend/agents/requirements_agent/pipeline/llm_adapter.py
backend/tests/test_requirements_agent_llm_adapter.py
```

### 포함해야 하는 기능

- `LLM_MODE=stub` 지원
- `LLM_MODE=vertex` 지원 준비
- prompt 파일 로딩
- JSON 응답 파싱
- schema contract 위반 시 명확한 error 반환
- 테스트에서는 network 호출 금지
- API key 또는 credential 값을 로그에 출력하지 않음

### 사용 env 후보

```text
LLM_MODE=stub|vertex
GCP_PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS=
VERTEX_LOCATION=asia-northeast3
VERTEX_MODEL=gemini-2.5-pro
```

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 3 작업을 진행해줘.
llm_adapter.py와 LLM adapter 테스트 파일을 생성해줘.
stub mode와 vertex mode를 같은 interface로 다룰 수 있게 하고,
테스트에서는 외부 네트워크 호출 없이 fake adapter로 contract를 검증하게 해줘.
credential 값은 절대 출력하지 말고, 설정 누락은 명확한 error로 반환하게 해줘.
```

### 완료 기준

- LLM adapter 파일 생성
- LLM adapter 테스트 생성
- 실제 API 호출부와 테스트 fake가 분리됨

## File Create Phase 4. Vertex Requirements Extractor 파일 생성

### 목표

Vertex Gemini를 사용해 section별 raw requirement 후보를 추출하는 extractor 파일을 생성한다.

### 생성 대상

```text
backend/agents/requirements_agent/pipeline/vertex_requirements_extractor.py
```

### 포함해야 하는 기능

- `requirements_extractor_prompt.md` 로딩
- section 단위 payload 입력
- PRD section 원문 요약 금지
- source evidence 필수 요청
- unknown/missing/low confidence 분리 원칙 유지
- Vertex 응답을 `run_section_extraction` contract에 맞게 normalize
- LLM이 최종 `Requirements_List.json` 필드를 반환하면 거부
- API 호출 실패 시 phase error로 반환

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 4 작업을 진행해줘.
vertex_requirements_extractor.py를 생성해줘.
requirements_extractor_prompt.md를 사용해서 section 단위 raw requirement 후보를 추출하고,
source evidence 필수, PRD 요약 금지, unknown/low confidence 분리 원칙을 지켜줘.
LLM이 최종 Requirements_List 필드를 만들려고 하면 거부되게 해줘.
```

### 완료 기준

- Vertex extractor 파일 생성
- `run_section_extraction`에 주입 가능한 callable 제공
- prompt/schema contract가 코드에 반영됨

## File Create Phase 5. Local Runner 파일 생성

### 목표

PRD PDF, `datasets/raw`, LLM mode를 받아 Requirements Agent Phase 1~10을 한 번에 실행하는 local runner 파일을 생성한다.

### 생성 대상

```text
backend/agents/requirements_agent/pipeline/run_requirements_agent_local.py
backend/tests/test_requirements_agent_local_runner.py
```

### 목표 명령

```powershell
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local `
  --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" `
  --employee-data-dir "datasets/raw" `
  --llm-mode stub `
  --write-outputs
```

실제 LLM 실행 목표 명령:

```powershell
.venv\Scripts\python.exe -m backend.agents.requirements_agent.pipeline.run_requirements_agent_local `
  --prd "backend/agents/requirements_agent_민성초기세팅/PRD/PRD_001_notification_center.pdf" `
  --employee-data-dir "datasets/raw" `
  --llm-mode vertex `
  --write-outputs
```

### 포함해야 하는 기능

- `--prd`
- `--employee-data-dir`
- `--llm-mode stub|vertex`
- `--human-confirm-decision`
- `--write-outputs`
- `--output-dir`
- 실행 summary 출력
- schema validation 결과 출력
- selected column과 실제 CSV header 충돌 여부 출력
- output 파일 생성 목록 출력
- 실패 phase와 error reason 출력

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 5 작업을 진행해줘.
run_requirements_agent_local.py와 local runner 테스트 파일을 생성해줘.
PRD PDF, datasets/raw, llm-mode, human-confirm-decision, write-outputs 옵션을 받아
기존 requirements_pipeline.py를 실행하게 해줘.
stub mode로 먼저 검증 가능하고, vertex mode에서는 LLM adapter를 통해 실제 section extraction을 수행할 수 있게 해줘.
```

### 완료 기준

- local runner 파일 생성
- local runner 테스트 생성
- stub/vertex mode 선택 가능
- outputs 생성 옵션 명확화

## File Create Phase 6. Output Policy 테스트 파일 생성

### 목표

outputs 파일이 runner 실행 결과로만 생성되는지 검증하는 테스트 파일을 생성한다.

### 생성 대상

```text
backend/tests/test_requirements_agent_finish_outputs.py
```

### 포함해야 하는 검증

- `write_outputs=False`면 outputs 미생성
- `write_outputs=True`면 10개 output 생성
- `Requirements_List.json` schema validation 통과
- output JSON이 비어 있지 않음
- selected column이 실제 CSV header와 충돌하지 않음

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 6 작업을 진행해줘.
test_requirements_agent_finish_outputs.py를 생성해줘.
write_outputs=False에서는 outputs 파일이 생성되지 않고,
write_outputs=True에서는 10개 output JSON이 생성되며,
Requirements_List.json schema validation과 selected column CSV header 검증까지 수행하게 해줘.
```

### 완료 기준

- output policy 테스트 파일 생성
- outputs 생성 정책이 테스트로 고정됨

## File Create Phase 7. Human Confirm Decision 템플릿 생성

### 목표

실제 output 검토 후 사용할 Human Confirm decision 템플릿을 생성한다.

### 생성 대상

```text
backend/agents/requirements_agent/local_inputs/human_confirm_decision_prd_001.json
```

### 주의

이 파일은 Phase 4~5에서 실제 unknown/missing/invalid/low confidence 항목을 확인한 뒤 생성하는 것을 권장한다.

초기 생성 시에는 빈 결정 구조만 둔다.

### 기본 구조

```json
{
  "project_specific_mapping": {},
  "removed_items": [],
  "updated_project_fields": {},
  "confirmed_restricted_column_keys": [],
  "confirmed_unknown_requirements": [],
  "notes": []
}
```

### 작업 지시 요청 멘트

```text
Requirements Agent 마무리 파일 생성 Phase 7 작업을 진행해줘.
local_inputs/human_confirm_decision_prd_001.json 템플릿을 생성해줘.
아직 실제 unknown/missing/invalid 항목을 확정하기 전이므로 빈 decision 구조만 만들고,
전역 taxonomy/rulebase는 수정하지 않게 해줘.
```

### 완료 기준

- Human Confirm decision 템플릿 생성
- 전역 reference 파일 변경 없음

## 6. 추천 생성 순서

| 순서 | Phase | 생성 대상 | 이유 |
|---:|---|---|---|
| 1 | Phase 0 | 없음 | 현재 없는 파일만 확정 |
| 2 | Phase 1 | `local_inputs/` | Human Confirm 보조 입력 위치 확보 |
| 3 | Phase 2 | `local_input_loader.py`, loader test | PRD/DB input이 먼저 안정화되어야 함 |
| 4 | Phase 3 | `llm_adapter.py`, adapter test | LLM 연결 interface 확정 |
| 5 | Phase 4 | `vertex_requirements_extractor.py` | 실제 LLM extraction 연결 |
| 6 | Phase 5 | `run_requirements_agent_local.py`, runner test | 전체 실행 진입점 생성 |
| 7 | Phase 6 | output policy test | outputs 생성 정책 고정 |
| 8 | Phase 7 | Human Confirm decision template | 실제 output 검토 후 사용 |

## 7. 최종 파일 생성 완료 기준

파일 생성 단계 완료 기준은 다음과 같다.

- 로컬 PRD/DB input을 읽을 파일이 준비됐다.
- LLM API 연결 interface 파일이 준비됐다.
- Vertex Gemini extractor 파일이 준비됐다.
- local runner 파일이 준비됐다.
- loader, adapter, runner, output policy 테스트 파일이 준비됐다.
- Human Confirm decision을 둘 폴더가 준비됐다.
- outputs JSON은 손으로 만들지 않고 runner 실행 산출물로 남겨뒀다.

## 8. 주의사항

- 실제 API key나 service account JSON 내용을 파일에 직접 쓰지 않는다.
- `.env`에는 credential 경로와 모델 설정만 둔다.
- 테스트에서는 외부 LLM API를 호출하지 않는다.
- Vertex mode 실행은 credential 준비 후 수동 또는 명시 요청 시에만 수행한다.
- PDF 원문은 요약하지 않는다.
- outputs JSON은 이 파일 생성 단계에서 만들지 않는다.
- Human Confirm decision은 전역 taxonomy 수정이 아니라 프로젝트 전용 결정만 담는다.

