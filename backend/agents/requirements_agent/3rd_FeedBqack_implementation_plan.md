# 3rd FeedBack Implementation Plan

## 1. 목적

이 문서는 Requirements Agent의 3차 품질 보완 계획이다. 목표는 현재 알림 센터 PRD에만 맞춘 보정이 아니라, 일반적인 웹/앱/SaaS/모바일/데이터/AI/운영성 PRD가 들어와도 `Requirements_List.json`, 직원/팀 ranking, Shadow RolePlay 입력이 안정적으로 생성되도록 하는 것이다.

핵심 개선 구조는 다음과 같다.

```text
PRD
-> Project Field Extraction
-> Vertex Extraction
-> Candidate Normalization
-> Rule-based Matching
-> Vertex Suggested Mapping
-> Taxonomy/Rulebase Validation
-> Auto Confirm or Human Confirm
-> Requirements_List
-> Employee/Team Ranking
-> Shadow RolePlay Vertex Strict Verification
```

## 2. 현재 확인된 문제

| 문제 | 원인 | 목표 |
|---|---|---|
| `project_name`이 `PRD:`로 잡힘 | PDF text 추출 후 첫 짧은 줄을 제목으로 선택 | `제목`, `Title`, 첫 heading, Document Meta title 우선 |
| `project_goal` 누락 | 영어 `goal/objective/purpose` prefix만 인식 | `TL;DR`, `비즈니스 목표`, `사용자 목표`, `목표로 합니다`, `G1/G2` 인식 |
| `duration_weeks` 누락 | `6 weeks`만 인식하고 `6주`, sprint 표현 미지원 | `6주`, `W1-W6`, `3 스프린트`, `1 스프린트 = 2주` 처리 |
| 예산 없음이 missing 처리됨 | `budget: null`을 무조건 missing으로 분류 | 명시적 예산 없음은 valid absent budget으로 처리 |
| unknown requirement 다수 | Vertex는 추출만 하고 taxonomy/rulebase가 단독 매칭 | Vertex suggested mapping + rule validation 추가 |
| 짧은 후보가 unknown으로 남음 | `발송`, `실패율`, `활성화` 같은 단편 후보 후처리 없음 | evidence 주변 문맥과 병합해 의미 단위로 정규화 |
| RolePlay vertex 검증 불명확 | vertex 실패 시 stub fallback 가능 | strict mode에서 fallback을 실패로 처리 |

## 3. Phase별 구현 계획

## Phase 1. Project Field Extraction 보강

- 한국어/영어 PRD 메타 파서를 보강한다.
- `PRD:` 같은 generic heading은 project name으로 확정하지 않는다.
- `제목`, `Title`, `Document Meta`, markdown H1을 우선한다.
- `TL;DR`, `목표로 합니다`, `비즈니스 목표`, `사용자 목표`, `G1/G2`에서 project goal을 추출한다.
- `duration_weeks`는 `6주`, `W1-W6`, `3 스프린트`, `1 스프린트 = 2주`를 주 단위로 환산한다.
- `예산: 별도 추가 인프라 비용 없음`은 `budget: null`로 두되 `missing_fields`에 포함하지 않는다.

## Phase 2. Candidate Normalization 추가

- extraction 결과와 source evidence를 입력받아 short/generic 후보를 정규화한다.
- `발송`, `실패율`, `활성화`, `권한`, `처리`, `연동` 등은 evidence 주변 문맥과 병합한다.
- normalized candidate는 original candidate id, source evidence, merge reason을 보존한다.
- 병합 불가 단편은 final required item으로 승격하지 않고 review bucket에 남긴다.

## Phase 3. Vertex-assisted Mapping 추가

- rule-based matching 이후 unresolved 후보만 Vertex suggested mapping에 보낸다.
- mapping mode는 `rule`, `llm_assisted`, `auto`를 지원한다.
- 기본값 `auto`는 stub 실행 시 rule-only, vertex/gemini 실행 시 llm-assisted로 동작한다.
- LLM 응답 필드는 다음으로 제한한다.

```json
{
  "candidate_id": "string",
  "suggested_target_type": "feature|constraint|role|skill",
  "suggested_target_key": "string",
  "confidence": 0.0,
  "reason": "string",
  "evidence_ids": ["string"]
}
```

- validation 기준은 target key 존재, item_type 일치, source evidence 존재, confidence `>= 0.88`이다.
- 검증 통과 항목은 auto confirmed로 처리하고, 실패 항목은 Human Confirm으로 보낸다.
- Vertex suggested mapping은 taxonomy를 자동 수정하지 않는다.

## Phase 4. Taxonomy/Rulebase 0.3.0 고도화

- 웹/앱/SaaS/모바일/데이터/AI/운영성 PRD 범위를 우선 지원한다.
- core app, commerce, mobile, data/AI, infra, security, delivery, business constraints 도메인을 확장한다.
- staffing role과 stakeholder role을 구분한다.
- 직원 ranking에는 staffing role만 사용하고, stakeholder role은 RolePlay risk/context로 보존한다.
- reference version을 `0.3.0`으로 올리고 `auto_extend_taxonomy=false`를 유지한다.

## Phase 5. Human Confirm 연계 보강

- rejected/ambiguous suggested mapping reason을 Human Confirm packet에 포함한다.
- 사용자가 승인한 mapping만 `project_specific_mapping`으로 반영한다.
- 전역 taxonomy/rulebase는 Human Confirm 결과로 자동 수정하지 않는다.
- Human Confirm 완료 전에는 status를 `needs_human_confirm`으로 유지한다.

## Phase 6. RolePlay Vertex Strict 검증

- requirements local runner에 `--roleplay-strict-llm` 옵션을 추가한다.
- Shadow RolePlay runner와 RoleAgent까지 strict flag를 전달한다.
- strict mode에서 Vertex 호출 실패, JSON parse 실패, credential 누락, fallback 발생은 실패로 처리한다.
- summary에 actual llm mode, vertex turn count, fallback count를 기록한다.

## 4. 산출물 변경

| 산출물 | 변경 |
|---|---|
| `Mapped_Requirements.json` | normalization trace, suggested mapping trace 추가 |
| `Human_Confirm_Result.json` | rejected/ambiguous suggested mapping 포함 |
| `Requirements_List.json` | 명시적 예산 없음은 `budget: null`, `missing_fields`에서 budget 제외 |
| `Roleplay_Simulation_Input_Packet.json` | 보정된 project field 반영 |
| `Orchestrator_Output.json` | actual LLM mode, vertex turn count, fallback count 기록 |

## 5. 테스트 기준

- `PRD:`를 project name으로 잡지 않는다.
- `제목 | 실시간 알림 센터 PRD`를 project name으로 잡는다.
- `TL;DR`, `비즈니스 목표`, `목표로 합니다`에서 project goal을 추출한다.
- `기간: 6주`, `3 스프린트`, `W1-W6`를 duration으로 변환한다.
- `예산: 별도 추가 인프라 비용 없음`은 missing budget으로 처리하지 않는다.
- short candidate는 source evidence와 병합되며 source evidence를 유지한다.
- LLM suggested mapping은 taxonomy key가 존재할 때만 자동 확정된다.
- unknown requirement count는 PRD_001 기준 `<= 10`을 목표로 한다.
- strict RolePlay vertex 실행은 실제 vertex mode를 증명하거나 명확히 실패해야 한다.

## 6. 범위와 가정

- 이번 일반화 범위는 웹/앱/SaaS/모바일/데이터/AI/운영성 프로젝트다.
- 의료, 법률, 금융 규제 전문 PRD나 하드웨어/제조 PRD는 이번 taxonomy 0.3.0 핵심 범위에서 제외한다.
- Vertex는 최종 판단자가 아니라 suggested mapping 생성자다.
- Taxonomy/rulebase는 표준 key 검증자다.
- Human Confirm은 애매한 항목의 최종 승인자다.
