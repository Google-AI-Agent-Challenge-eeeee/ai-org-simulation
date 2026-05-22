# Requirements Agent Initial File Create Implementation Plan

## 0. 문서 목적

이 문서는 `backend/agents/requirements_agent/` 초기 구현 파일을 어떤 순서로 생성할지 정리한 작업 계획서다.

대상은 초기 구현에 필요한 기준표, schema, prompt, rule-based module, pipeline 파일이다.  
`outputs/` 아래 JSON 파일은 pipeline 실행 산출물이므로 초기 수동 생성 대상에서 제외한다.

## 1. 작업 루트

```text
backend/agents/requirements_agent/
```

현재 준비된 하위 폴더:

```text
prompts/
pipeline/
modules/
schemas/
references/
outputs/
```

## 2. 전체 생성 대상

| 구분 | 생성 위치 | 생성 파일 수 |
|---|---|---:|
| Reference 기준표 | `references/` | 3 |
| Schema 계약 | `schemas/` | 3 |
| LLM Prompt | `prompts/` | 3 |
| Rule-based Modules | `modules/` | 5 |
| Pipeline | `pipeline/` | 5 |

총 초기 생성 대상은 19개다.

## 3. 추천 작업 순서

| 순서 | Phase | 작업 묶음 | 이유 |
|---:|---|---|---|
| 1 | Phase 1 | Reference 기준표 | taxonomy, rulebase, column rule이 후속 판단 기준이 된다. |
| 2 | Phase 2 | Schema 계약 | 중간 산출물과 최종 산출물의 구조를 먼저 고정한다. |
| 3 | Phase 3 | LLM Prompt | schema와 reference 기준에 맞춰 LLM 출력 흔들림을 줄인다. |
| 4 | Phase 4 | Rule-based Modules | reference/schema 기반으로 독립 구현과 테스트가 가능하다. |
| 5 | Phase 5 | Pipeline | 마지막에 전체 phase 흐름을 연결한다. |

---

## Phase 1. Reference 기준표 생성

### 작업 지시 요청멘트

```text
Requirements Agent Phase 1 작업을 진행해줘.
초기 reference 기준표 3개를 생성해줘.
taxonomy/rulebase/employee column rule은 MVP 웹/앱 프로젝트 요구사항 분석 기준으로 작성하고,
unknown requirement를 자동으로 taxonomy에 추가하지 않는 원칙을 반영해줘.
```

### 생성 파일

| 파일 | 생성 위치 | 목적 |
|---|---|---|
| `taxonomy.json` | `references/taxonomy.json` | 표준 feature별 role, skill, risk, weight hint 정의 |
| `rulebase.json` | `references/rulebase.json` | PRD 표현 alias를 taxonomy 표준 feature로 매핑 |
| `employee_column_rules.json` | `references/employee_column_rules.json` | 요구사항 유형별 직원 DB column 선택 규칙 |

### 참고 자료

| 자료 | 위치 | 참고 내용 |
|---|---|---|
| Rules 문서 | `requirements_agent_docs/requirements_agent_rules.md` | taxonomy, unknown, column rule |
| I/O Schema 문서 | `requirements_agent_docs/requirements_agent_io_schema.md` | 최종 output 필드와 후속 사용처 |
| Column 설명 | `column_explain/column_explain.md` | 직원 DB column 의미 |
| Raw DB 샘플 | `DB_DataSet/*/*.csv` | 실제 column 후보 확인 |
| 기존 raw dataset | `datasets/raw/*/*.csv` | repo 표준 더미 데이터 위치 |

### 완료 기준

- `taxonomy.json`에 MVP 표준 feature가 정의되어 있다.
- `rulebase.json`에 주요 alias가 표준 feature로 연결되어 있다.
- `employee_column_rules.json`에 기술, 일정, 비용, GitHub, Jira, Slack, Calendar 기준 column rule이 있다.
- taxonomy에 없는 요구사항은 unknown으로 분리하는 전제가 유지된다.

---

## Phase 2. Schema 계약 생성

### 작업 지시 요청멘트

```text
Requirements Agent Phase 2 작업을 진행해줘.
중간 결과와 최종 결과의 JSON Schema 3개를 생성해줘.
최종 Requirements_List.json은 후속 직원 적합도 계산과 Shadow RolePlay 입력으로 바로 사용할 수 있게 해줘.
```

### 생성 파일

| 파일 | 생성 위치 | 목적 |
|---|---|---|
| `requirements_schema.json` | `schemas/requirements_schema.json` | 최종 `Requirements_List.json` 구조 |
| `extracted_requirements_draft_schema.json` | `schemas/extracted_requirements_draft_schema.json` | section/chunk 추출 후보 병합 결과 구조 |
| `mapped_requirements_schema.json` | `schemas/mapped_requirements_schema.json` | taxonomy/rulebase 매핑 결과 구조 |

### 참고 자료

| 자료 | 위치 | 참고 내용 |
|---|---|---|
| I/O Schema 문서 | `requirements_agent_docs/requirements_agent_io_schema.md` | final/intermediate output 필드 |
| Phase Flow 문서 | `requirements_agent_docs/requirements_agent_phase_flow.md` | phase별 input/output |
| Test Plan 문서 | `requirements_agent_docs/requirements_agent_test_plan.md` | acceptance criteria와 edge case |

### 완료 기준

- 최종 schema에 아래 필드가 포함된다.
  - `project_name`
  - `project_goal`
  - `required_features`
  - `required_roles`
  - `required_skills`
  - `duration_weeks`
  - `budget`
  - `constraints`
  - `risk_factors`
  - `selected_employee_columns`
  - `column_weights`
  - `column_priority_order`
  - `weighting_reason`
  - `unknown_requirements`
  - `missing_extractions`
  - `missing_fields`
  - `low_confidence_items`
  - `coverage_check`
- draft schema는 source evidence와 confidence를 표현할 수 있다.
- mapped schema는 matched/unknown/conflict 상태를 표현할 수 있다.

---

## Phase 3. LLM Prompt 생성

### 작업 지시 요청멘트

```text
Requirements Agent Phase 3 작업을 진행해줘.
LLM 호출용 prompt 3개를 생성해줘.
PRD 원문은 요약하지 않고 section 단위로 입력받는다는 원칙,
source evidence 필수 원칙,
unknown/missing/low confidence 분리 원칙을 반영해줘.
```

### 생성 파일

| 파일 | 생성 위치 | 목적 |
|---|---|---|
| `requirements_extractor_prompt.md` | `prompts/requirements_extractor_prompt.md` | PRD section에서 raw 요구사항 후보 추출 |
| `validator_agent_prompt.md` | `prompts/validator_agent_prompt.md` | missing, invalid, low confidence 검증 |
| `Column_Explain_Prompt.md` | `prompts/Column_Explain_Prompt.md` | 직원 DB column 의미 설명 및 column 판단 보조 |

### 참고 자료

| 자료 | 위치 | 참고 내용 |
|---|---|---|
| Guardrails 문서 | `requirements_agent_docs/requirements_agent_guardrails.md` | 오탐/미탐/token/개인정보 guardrail |
| Token Verify 문서 | `Token_Verify/Token_limit_Verify_phase.md` | lossless-first, section/chunk 원칙 |
| Column 설명 | `column_explain/column_explain.md` | column explain prompt 원본 후보 |
| 공용 Column 설명 | `packages/prompts/requirement/column_explain.md` | repo 공용 prompt 후보 |
| Schema 파일 | `schemas/*.json` | prompt 출력 형식 기준 |

### 완료 기준

- extractor prompt는 최종 `Requirements_List.json`을 만들지 않고 후보만 추출하게 한다.
- validator prompt는 단독 삭제가 아니라 Human Confirm 대상으로 분리하게 한다.
- 모든 추출 후보에 source evidence를 요구한다.
- PRD 원문 요약본만 입력하는 방식은 금지한다.

---

## Phase 4. Rule-based Modules 생성

### 작업 지시 요청멘트

```text
Requirements Agent Phase 4 작업을 진행해줘.
LLM 없이 동작 가능한 rule-based module 5개를 생성해줘.
각 모듈은 reference/schema 파일을 기준으로 입력을 받고,
후속 pipeline에서 조합할 수 있도록 순수 함수 중심으로 작성해줘.
```

### 생성 파일

| 파일 | 생성 위치 | 목적 |
|---|---|---|
| `taxonomy_matcher.py` | `modules/taxonomy_matcher.py` | raw 요구사항을 taxonomy/rulebase 기준으로 매핑하고 unknown 분리 |
| `column_selection_draft.py` | `modules/column_selection_draft.py` | 요구사항 기준 직원 DB column 후보 선택 |
| `coverage_check.py` | `modules/coverage_check.py` | PRD section별 covered/partial/missing 계산 |
| `column_weighting_final.py` | `modules/column_weighting_final.py` | Human Confirm 이후 최종 column weight 계산 |
| `requirements_list_builder.py` | `modules/requirements_list_builder.py` | 최종 `Requirements_List.json` 구조 조립 및 validation |

### 참고 자료

| 자료 | 위치 | 참고 내용 |
|---|---|---|
| Reference 파일 | `references/*.json` | taxonomy/rulebase/column rule 기준 |
| Schema 파일 | `schemas/*.json` | 입출력 검증 기준 |
| Rules 문서 | `requirements_agent_docs/requirements_agent_rules.md` | 각 rule의 판단 기준 |
| Test Plan 문서 | `requirements_agent_docs/requirements_agent_test_plan.md` | rule별 테스트 포인트 |

### 완료 기준

- taxonomy matcher는 억지 매핑을 하지 않고 unknown을 분리한다.
- column selection은 draft만 만들고 final weight를 확정하지 않는다.
- coverage check는 section map 기준으로 상태를 계산한다.
- weighting final은 Human Confirm 이후 확정 요구사항 기준으로 계산한다.
- final builder는 schema validation을 통과하는 구조를 만든다.

---

## Phase 5. Pipeline 생성

### 작업 지시 요청멘트

```text
Requirements Agent Phase 5 작업을 진행해줘.
Requirements Agent pipeline 파일 5개를 생성해줘.
PRD 원문 보존, semantic section split, section extraction, validation, final build 순서로 연결하고,
outputs/*.json은 pipeline 실행 산출물로만 생성되게 해줘.
```

### 생성 파일

| 파일 | 생성 위치 | 목적 |
|---|---|---|
| `token_limit_verify.py` | `pipeline/token_limit_verify.py` | token budget 계산, hard limit gate, chunk action 결정 |
| `section_splitter.py` | `pipeline/section_splitter.py` | PRD/PM 문서를 semantic section 단위로 분리 |
| `extraction_runner.py` | `pipeline/extraction_runner.py` | section별 추출 실행 및 draft 병합 준비 |
| `validation_runner.py` | `pipeline/validation_runner.py` | validator 실행 결과 정리 |
| `requirements_pipeline.py` | `pipeline/requirements_pipeline.py` | 전체 Requirements Agent phase orchestration |

### 참고 자료

| 자료 | 위치 | 참고 내용 |
|---|---|---|
| Phase Flow 문서 | `requirements_agent_docs/requirements_agent_phase_flow.md` | Phase 0~10 전체 흐름 |
| Token Verify 문서 | `Token_Verify/Token_limit_Verify_phase.md` | token budget, section/chunk gate |
| API Spec 문서 | `requirements_agent_docs/requirements_agent_api_spec.md` | 향후 API 연결점 |
| Modules 파일 | `modules/*.py` | pipeline에서 호출할 rule-based 기능 |
| Prompts 파일 | `prompts/*.md` | LLM runner에서 사용할 prompt |

### 완료 기준

- pipeline은 아래 흐름을 따른다.

```text
Input Document
→ Token Limit Verify
→ Section Splitter
→ Section Requirements Extraction
→ Chunk Result Merge
→ Taxonomy Matching
→ Column Selection Draft
→ Validation
→ Coverage Check
→ Human Confirm
→ Column Weighting Final
→ Requirements List Builder
```

- `outputs/*.json`은 초기 수동 파일이 아니라 실행 결과로 생성된다.
- 각 phase는 중간 결과를 구조화된 dict 또는 schema-compatible object로 넘긴다.

---

## 4. 생성 제외 대상

아래 파일들은 초기 생성 대상이 아니라 pipeline 실행 산출물이다.

| 제외 파일 | 위치 |
|---|---|
| `Cleaned_PRD_Text.json` | `outputs/` |
| `Section_Extraction_Result.json` | `outputs/` |
| `Extracted_Requirements_Draft.json` | `outputs/` |
| `Mapped_Requirements.json` | `outputs/` |
| `Column_Selection_Draft.json` | `outputs/` |
| `Validation_Result.json` | `outputs/` |
| `Coverage_Check_Result.json` | `outputs/` |
| `Human_Confirm_Result.json` | `outputs/` |
| `Column_Weighting_Result.json` | `outputs/` |
| `Requirements_List.json` | `outputs/` |

## 5. 커밋 전략

README convention을 따른다.

브랜치:

```text
agent/feat/requirements-agent
```

추천 커밋 단위:

```text
agent/feat: add requirements agent references
agent/feat: add requirements agent schemas
agent/feat: add requirements agent prompts
agent/feat: add requirements agent rule modules
agent/feat: add requirements agent pipeline
```

작업 중 테스트를 추가하면:

```text
agent/test: cover requirements agent modules
```
