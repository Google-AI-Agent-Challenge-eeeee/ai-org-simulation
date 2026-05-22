# Shadow_RolePlay_Agent Docs

이 폴더는 `Final_shdow_roleplay_agent_implementation_plan.md` 원본을 유지한 상태에서, Shadow_RolePlay_Agent 구현 중 자주 참조하고 수정해야 하는 세부 명세를 분리해 관리하기 위한 문서 폴더다.

원본 파일의 역할:

```text
../Final_shdow_roleplay_agent_implementation_plan.md
→ Shadow_RolePlay_Agent의 전체 목적, 아키텍처, 구현 방향, 우선순위를 설명하는 메인 implementation plan
```

이 폴더의 역할:

```text
shadow_roleplay_agent_docs/
→ 실제 구현 중 자주 바뀌는 I/O, rule, phase, command, API, test, guardrail을 분리 관리
```

## 문서 구성

| 파일 | 역할 |
|---|---|
| `shadow_roleplay_agent_io_schema.md` | Shadow_RolePlay_Agent의 입력, 중간 산출물, 최종 출력 schema 명세 |
| `shadow_roleplay_agent_rules.md` | issue/risk 평가 rule, score, verdict 기준 |
| `shadow_roleplay_agent_phase_flow.md` | Phase 0~10 구현 흐름, 각 phase의 목적/입력/출력/점검사항 |
| `shadow_roleplay_agent_phase_commands.md` | phase별 작업 지시 요청 멘트와 필수 참조 파일 |
| `shadow_roleplay_agent_architecture_notes.md` | 세부 아키텍처와 설계 근거 정리 |
| `shadow_roleplay_agent_api_spec.md` | Shadow RolePlay 관련 API endpoint 명세 |
| `shadow_roleplay_agent_test_plan.md` | 테스트 시나리오, edge case, acceptance criteria |
| `shadow_roleplay_agent_guardrails.md` | 개인정보, hallucination, evidence, scoring 관련 주의사항 |

## 관리 원칙

- 전체 설계 변경은 `Final_shdow_roleplay_agent_implementation_plan.md`에 반영한다.
- 구현 중 자주 바뀌는 schema, rule, phase, test는 이 폴더의 세부 문서에서 관리한다.
- 원천 업무 DB 직접 사용 금지, snapshot/summary/evidence 기반 입력 원칙을 유지한다.
- Token 관련 공통 정책은 루트의 `Token_limit_Verify_phase.md`를 함께 참조한다.
