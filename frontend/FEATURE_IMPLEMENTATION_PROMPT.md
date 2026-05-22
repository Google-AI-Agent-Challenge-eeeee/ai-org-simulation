# Frontend 기능 확장 구현 프롬프트

> **용도**: AI/개발자가 `frontend/` 코드를 수정·추가할 때 참조하는 기능 명세서  
> **디자인**: Stitch 목업 이미지는 `frontend/design/` 폴더에 별도 첨부 (아래 경로 참조)  
> **Mock 모드**: `NEXT_PUBLIC_MOCK=true` 유지 — 백엔드 없이 전체 플로우 동작해야 함

---

## 디자인 이미지 참조 (별도 첨부)

| 화면 | 이미지 경로 (예정) | 라우트 |
|------|-------------------|--------|
| 입력 | `design/01-simulate-input.png` | `/simulate` |
| 요구사항 검토 | `design/02-requirements-review.png` | `/session/[id]/requirements` |
| 팀 선택 | `design/03-team-selection.png` | `/session/[id]/teams` |
| 시뮬레이션 세션 | `design/04-simulation-session.png` | `/session/[id]` |
| 최종 리포트 | `design/05-report.png` | `/report/[id]` |

이미지가 없을 때는 본 문서의 **기능 설명**과 **컴포넌트 스펙**을 우선 따른다.

---

## 현재 vs 목표

### 현재 플로우 (AS-IS)

```
/simulate (PRD + PM 우선순위 칩)
  → POST /api/sessions
  → /session/[id] (킥오프 회의 SSE, 자동 진행)
  → /report/[id]
```

- PM은 프리셋 칩(속도/품질/균형) + 선택적 추가 텍스트만 입력
- 요구사항 분석 결과 확인·수락 단계 없음
- 팀 자동 선정 — PM이 팀을 고르지 않음
- 세션은 Kickoff 1단계만 표현 (`SessionHeader` 고정 문구)
- 백엔드 파이프라인 진행 상황 UI 없음

### 목표 플로우 (TO-BE)

```
/simulate
  → PM 페르소나(이름·말투·성향) + PRD + 운영 우선순위 입력
  → POST /api/sessions
  → /session/[id]/requirements   ← 요구사항 분석 시각화 + PM 수락/재검토
  → /session/[id]/teams          ← 상위 10팀 나열, PM 1팀 선택
  → /session/[id]                ← 5단계 SDLC 오케스트레이션 SSE
  → /report/[id]
```

**핵심 원칙**
- PM은 **직원 DB에 없음** — 사용자가 입력한 페르소나가 롤플레이 PM 발언 스타일에 주입됨
- PRD 입력 후 **바로 시뮬레이션 시작하지 않음** — Requirements Accept → Team Select 게이트 필수
- 오케스트레이터 **5단계**: Kickoff → Design → Development → Integration → QA/Release
- 화면 하단 **BackendStatusStrip**: 회색 monospace 로그로 백엔드 진행 단계 실시간 표시

---

## 기능 1: PM 페르소나 입력 (수정)

### 설명
사용자 본인이 PM 역할을 맡는다. 직원 DB에 PM 레코드가 없으므로, 이름·말투·성향·의사결정 스타일을 직접 입력해 이후 Role Play에 반영한다.

### 수정 대상
| 파일 | 작업 |
|------|------|
| `components/input/PmStyleCard.tsx` | **분리·확장** → `PmPersonaCard.tsx` + `PmPriorityCard.tsx` |
| `app/simulate/page.tsx` | 카드 3개 조립 (PRD / PM 페르소나 / PM 운영 우선순위) |
| `hooks/useInputForm.ts` | 상태·validation·submit payload 확장 |
| `lib/types.ts` | `SimulationInput`, `PmPersona` 타입 추가 |

### UI 스펙 — `PmPersonaCard`

```
Card title: "PM 페르소나"
Info banner (indigo/10): "PM은 직원 DB에 없습니다. 아래 입력이 롤플레이 PM 발언 스타일에 반영됩니다."

Fields:
1. pmName (required) — Input, placeholder "이름 (예: 김지은)"
2. pmPreset — 4 chips: 속도 우선 | 품질 우선 | 균형 | 직접 입력
3. pmPersona (required) — Textarea 4 rows
   placeholder: "말투, 성향, 의사결정 스타일..."
4. pmConstraints (optional) — Textarea 2 rows
   placeholder: "추가 조직 제약 (선택)"
```

### UI 스펙 — `PmPriorityCard` (기존 PmStyleCard 역할 축소)

```
Card title: "PM 운영 우선순위"
Note: "요구사항 분석 시 가중치에 반영됩니다"
- 동일 4 preset chips + optional extra textarea
```

### Validation
- `isValid`: `prd.trim().length >= 20` **AND** `pmName.trim().length >= 1` **AND** `pmPersona.trim().length >= 10`
- CTA 문구: `"요구사항 분석 시작 →"` (기존 "시뮬레이션 시작" 변경)
- Submit 후 이동: `/session/${id}/requirements` (기존 `/session/${id}` 변경)

### 타입

```typescript
export interface PmPersona {
  name: string
  preset: PmStylePreset
  persona: string        // 말투·성향
  constraints?: string
}

export interface SimulationInput {
  prd: string
  pmPersona: PmPersona
  pmPriority: string     // preset + optional extra (기존 pmStyle 대체)
}
```

### Mock
- `sessionStore` 또는 `localStorage`에 `pmPersona` 저장
- Mock SSE/리포트에서 PM persona name을 채팅·리포트에 반영 (하드코딩 "김지수" → 사용자 입력값)

---

## 기능 2: 요구사항 분석 & PM 수락 (신규)

### 설명
PRD 제출 후 Requirements_Agent가 생성한 `Requirements_List` 요약을 시각화한다. PM은 **수락** 또는 **재검토 요청**을 선택한다. 수락 전까지 팀 매칭·시뮬레이션은 시작되지 않는다.

### 신규 파일
| 파일 | 역할 |
|------|------|
| `app/session/[id]/requirements/page.tsx` | 페이지 조립 |
| `hooks/useRequirementsReview.ts` | fetch + accept/reject 로직 |
| `components/requirements/RequirementsOverview.tsx` | 프로젝트 개요 카드 |
| `components/requirements/FeaturePriorityBoard.tsx` | P0/P1/P2 칸반 보드 |
| `components/requirements/RolesSkillsPanel.tsx` | 역할·스킬 pill 목록 |
| `components/requirements/MilestoneTimeline.tsx` | 일정 타임라인 |
| `components/requirements/RiskFlagsPanel.tsx` | 리스크 칩 (collapsible) |
| `components/requirements/PmReviewPanel.tsx` | 수락/재검토 CTA + 피드백 textarea |
| `components/layout/ProgressStepper.tsx` | 5단계 스텝퍼 (공통) |
| `components/layout/BackendStatusStrip.tsx` | 하단 백엔드 로그 (공통) |
| `lib/types.ts` | `RequirementsList`, `RequirementsSummary` 타입 |
| `lib/mock/requirements.ts` | Mock Requirements_List (sample JSON 기반) |

### UI 스펙

**레이아웃**: 2-column (desktop 60/40), mobile stack

**Left — 시각화**
1. **프로젝트 개요**: project_name, project_summary, tags (일정·역할 수·기능 수)
2. **필수 역할 & 스킬**: 두 column pill list
3. **기능 요구사항**: P0(빨강) / P1(amber) / P2(grey) 3-column board  
   - 각 feature card: name, assigned_role badge, estimated_days, dependency icon
4. **일정 & 마일스톤**: horizontal timeline
5. **리스크 플래그**: warning chips, collapsible

**Right — PM 검토 패널 (sticky)**
- 분석 신뢰도 progress bar (mock: 92%)
- PM 페르소나 요약 (avatar + name + preset chip)
- Textarea "수정 요청 사항 (선택)"
- Primary: `"✓ 요구사항 수락하고 팀 매칭 시작"`
- Secondary: `"↺ 재검토 요청"`
- Disclaimer: "수락 후 팀 조합 순위가 계산됩니다. 바로 시뮬레이션이 시작되지 않습니다."

**ProgressStepper** (상단):  
`입력 → 요구사항 검토(active) → 팀 선택 → 시뮬레이션 → 리포트`

### API (Mock 분기 포함 — `lib/api.ts`)

```typescript
GET  /api/sessions/{id}/requirements     → RequirementsSummary
POST /api/sessions/{id}/requirements/accept   body: { feedback?: string }
POST /api/sessions/{id}/requirements/revise   body: { feedback: string }
```

Mock:
- 페이지 마운트 시 1~2초 analyzing 상태 후 mock requirements 표시
- `accept` → `/session/${id}/teams` 이동
- `revise` → BackendStatusStrip에 "재분석 중…" 표시 후 requirements 갱신 (mock: 동일 데이터 재표시)

### BackendStatusStrip (이 화면)
```
Requirements_Agent: PRD 파싱 완료
역할·기술 스택 추출 중…
기능 우선순위(P0/P1/P2) 분류 완료
PM 페르소나 프롬프트 주입 완료
```

---

## 기능 3: 팀 조합 선택 — 상위 10팀 (신규)

### 설명
직원 적합도·팀 적합도 점수로 모든 조합을 계산한 뒤 **상위 10팀**을 내림차순 나열한다. PM이 **1팀을 선택**해야만 시뮬레이션이 시작된다.

### 신규 파일
| 파일 | 역할 |
|------|------|
| `app/session/[id]/teams/page.tsx` | 페이지 조립 |
| `hooks/useTeamSelection.ts` | fetch teams + select + confirm |
| `components/teams/TeamSummaryStrip.tsx` | 총 조합 수·PM 이름 요약 |
| `components/teams/TeamRankCard.tsx` | 개별 팀 카드 (rank, avatars, scores, risks) |
| `components/teams/TeamSelectionBar.tsx` | 하단 sticky 선택 확인 바 |
| `lib/types.ts` | `TeamCandidate`, `TeamSelectionState` |
| `lib/mock/teams.ts` | 상위 10팀 mock (sample_selected_team_record 기반 변형) |

### UI 스펙

**Summary strip**
- "총 조합 경우의 수: 1,247" | "분석 완료: 상위 10팀" | "PM: {pmName}"

**TeamRankCard** (×10, score desc)
```
[Rank badge]  [5 avatars + role tags]  [Metrics]  [Radio]

Rank: #1 gold / #2 silver / #3 bronze / #4-10 grey
Metrics:
  - team_fit_score (large, e.g. 84.6)
  - role_coverage_score, skill_coverage_score, availability_score (mini bars %)
  - team_risk_flags chips (max 2 + "+N")
Radio/select on right — #1 default selected with indigo border

#1 expanded: "왜 이 팀인가?" 2-line rationale + skill gap warnings
```

**Bottom sticky bar**
- Left: "1위 팀 선택됨 · 84.6점"
- Right: `"이 팀으로 시뮬레이션 시작 →"` (팀 미선택 시 disabled)

### API

```typescript
GET  /api/sessions/{id}/teams              → { totalCombinations, teams: TeamCandidate[] }
POST /api/sessions/{id}/teams/select         body: { teamId: string }
```

Mock:
- 10팀 생성, rank 1~10, score 84.6 → 71.2 descending
- #1 멤버: sample JSON (권원솔 PM, 안우빈 BE, …) 사용
- select 후 `/session/${id}` 이동 + `sessionStore.setSelectedTeam(team)`

### BackendStatusStrip
```
직원 적합도 DB 비교 중…
팀 조합 경우의 수 계산: 1,247 combinations
스코어 정렬 완료 — 상위 10팀 추출
대기 중 — PM 팀 선택 필요
```

---

## 기능 4: 5단계 시뮬레이션 세션 (수정)

### 설명
선택된 팀으로 Shadow Roleplay Orchestrator 5단계를 SSE로 스트리밍한다. Kickoff만이 아니라 Design / Development / Integration / QA-Release까지 phase stepper와 헤더 타이틀이 동적으로 변경된다.

### 수정 대상
| 파일 | 작업 |
|------|------|
| `app/session/[id]/page.tsx` | PhaseStepper, BackendStatusStrip, sidebar 추가 |
| `components/session/SessionHeader.tsx` | phase별 동적 타이틀 |
| `components/session/StatusBar.tsx` | 5-phase stepper + subPhase text |
| `hooks/useKickoff.ts` | → `useSimulation.ts` rename, phase/backendLog 이벤트 처리 |
| `lib/types.ts` | `SessionStage`, `SimulationPhase`, `BackendLogEntry` 확장 |
| `lib/constants.ts` | phase labels, backend log templates |
| `store/sessionStore.ts` | selectedTeam, currentPhase, backendLogs, pmPersona |
| `lib/mock/scenario.ts` | 5-phase status events + backend log events |

### SessionStage 확장

```typescript
export type SimulationPhase =
  | "kickoff"
  | "design"
  | "development"
  | "integration"
  | "qa_release"

export type SessionStage =
  | "idle"
  | "analyzing"
  | "requirements_review"  // requirements 페이지용
  | "team_selection"       // teams 페이지용
  | "team_ready"
  | "meeting"
  | "done"

// sessionStore 추가 필드
currentPhase: SimulationPhase | null
backendLogs: string[]       // 최근 5줄, 최신이 밝게
selectedTeam: TeamCandidate | null
pmPersona: PmPersona | null
```

### SSE 이벤트 확장

```
event: status
  → { stage, text, phase?: SimulationPhase, phaseIndex?: 1-5 }

event: backend_log
  → { text: string, timestamp?: string }

event: message
  → { persona, token, messageId, turnType?: "observation"|"concern"|"dependency"|"proposed_action" }

event: done
  → {}
```

### SessionHeader 타이틀 매핑
| phase | title |
|-------|-------|
| kickoff | 킥오프 회의 진행 중… |
| design | 설계 단계 진행 중… |
| development | 개발 단계 진행 중… |
| integration | 연동 단계 진행 중… |
| qa_release | QA/릴리즈 진행 중… |

### StatusBar
- 5-phase horizontal stepper (①~⑤)
- Sub-banner: `"Phase 2/5 · Design Phase · API/DB 스펙·기술 선택"`

### MeetingChat
- PM 메시지: `pmPersona.name` + purple avatar (MOCK_PERSONAS[0] name override)
- 선택된 팀 멤버 4명 avatar/color 사용
- turnType label optional (small muted badge on bubble)

### BackendStatusStrip (세션 화면 — 가장 중요)
고정 하단 48px, `font-mono text-xs text-zinc-500`

Mock emit 순서 예:
```
Simulation_Input_Packet 병합 중…
PrivacyColumnFilter · PII 컬럼 제거 완료
AgentCardBuilder · 5명 Agent Card 생성
ScenarioPhasePlanner · 리스크 기반 시나리오 13개 배치
Orchestrator · evt_001 backend_workload_concentration 처리 중
RoleAgent · BE 안우빈 observation 생성
Phase 2/5 Design Phase 시작
PhaseLogCollector · 이슈 4건, 결정 3건 집계
```

최신 줄: `text-zinc-400`, 이전 줄: `text-zinc-600`

### SessionFooter
- 문구: "5단계 시뮬레이션이 완료되면 리포트가 자동 생성됩니다"
- `stage === "done"` 일 때만 "리포트 보기 →" 활성

---

## 기능 5: 최종 리포트 보강 (수정)

### 설명
선택 팀·PM 페르소나·수락된 요구사항·5단계 요약을 리포트에 반영한다.

### 수정 대상
| 파일 | 작업 |
|------|------|
| `lib/types.ts` | `Report` 확장 |
| `lib/mock/scenario.ts` | MOCK_REPORT 확장 |
| `components/report/RequirementsSummarySection.tsx` | **신규** — collapsible |
| `components/report/MeetingSummarySection.tsx` | 5-phase timeline으로 변경 |
| `components/report/TeamSection.tsx` | PM 페르소나 note + rank badge |
| `app/report/[id]/page.tsx` | 새 섹션 조립 |

### Report 타입 확장

```typescript
export interface Report {
  // existing fields...
  pmPersona: PmPersona
  selectedTeam: {
    rank: number
    teamFitScore: number
    teamId: string
  }
  requirementsSummary?: {
    acceptedAt: string
    p0Count: number
    timelineDays: number
    riskFlagCount: number
  }
  phaseSummaries?: Array<{
    phase: SimulationPhase
    score: number
    summary: string
  }>
}
```

### UI 추가
1. **TeamSection**: "PM {name} (사용자 페르소나)" + "#{rank} · {score}점" badge
2. **RequirementsSummarySection** (collapsible): acceptedAt, P0 count, timeline, risk flags
3. **MeetingSummarySection** 제목 → "5단계 시뮬레이션 요약"  
   - 5 phase icon timeline, each 1-line + phase score badge

---

## 공통 컴포넌트

### `ProgressStepper`
```typescript
interface ProgressStepperProps {
  currentStep: "input" | "requirements" | "teams" | "simulation" | "report"
}
```
5 steps: 입력 → 요구사항 검토 → 팀 선택 → 시뮬레이션 → 리포트

### `BackendStatusStrip`
```typescript
interface BackendStatusStripProps {
  logs: string[]
  isActive?: boolean   // pulse dot when true
}
```
- `requirements`, `teams`, `session/[id]` 페이지 하단 고정
- `/simulate` 에서는 idle placeholder: "대기 중 — PRD와 PM 페르소나를 입력하세요"
- `sessionStore.backendLogs` 구독 또는 props

---

## API 레이어 변경 요약 (`lib/api.ts`)

| 함수 | 설명 |
|------|------|
| `createSession(input)` | payload에 pmPersona 포함, redirect는 hook에서 처리 |
| `fetchRequirements(sessionId)` | **신규** |
| `acceptRequirements(sessionId, feedback?)` | **신규** |
| `reviseRequirements(sessionId, feedback)` | **신규** |
| `fetchTeamCandidates(sessionId)` | **신규** |
| `selectTeam(sessionId, teamId)` | **신규** |
| `getStreamUrl(sessionId)` | 기존 유지 (팀 선택 후에만 호출) |
| `fetchReport(sessionId)` | 확장된 Report 반환 |

Mock 분기는 **반드시 `lib/api.ts`와 `lib/mock/` 내부에서만** 처리.

---

## sessionStore 확장 요약

```typescript
interface SessionStore {
  // existing...
  pmPersona: PmPersona | null
  selectedTeam: TeamCandidate | null
  requirementsAccepted: boolean
  currentPhase: SimulationPhase | null
  backendLogs: string[]

  setPmPersona: (p: PmPersona) => void
  setSelectedTeam: (t: TeamCandidate) => void
  setRequirementsAccepted: (v: boolean) => void
  setCurrentPhase: (p: SimulationPhase) => void
  appendBackendLog: (text: string) => void
  clearBackendLogs: () => void
}
```

---

## Mock 데이터 참조 (백엔드 sample JSON)

구현 시 아래 sample 파일 구조를 그대로 TypeScript 타입·mock 데이터 source로 사용:

```
backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples/
  sample_requirements_list.json      → lib/mock/requirements.ts
  sample_selected_team_record.json   → lib/mock/teams.ts (#1팀)
  sample_employee_fit_profile_snapshots.json
  sample_team_risk_summary.json
```

---

## 구현 순서 (권장)

1. **타입·store·constants** — `types.ts`, `sessionStore.ts`, `constants.ts`
2. **공통** — `ProgressStepper`, `BackendStatusStrip`
3. **기능 1** — PM 페르소나 입력 (`/simulate` 수정)
4. **기능 2** — Requirements review 페이지 + mock API
5. **기능 3** — Team selection 페이지 + mock API
6. **기능 4** — Session 5-phase + backend log SSE
7. **기능 5** — Report 섹션 보강
8. **implement.md** — 루트 문서 플로우 diagram 업데이트

---

## 클린 코드 규칙 (기존 유지)

- Page 파일: 조립만, 로직은 hook
- Mock 분기: `lib/api.ts` 단일 진입점
- 컴포넌트: Atomic Design 계층 유지 (`components/requirements/`, `components/teams/` 추가)
- 디자인 토큰: `bg-[#0f0f13]`, card `#1a1a22`, accent `#6366f1`, border `zinc-700/800`
- 이미지 제공 시: 해당 screen 컴포넌트 주석에 `@design design/0X-*.png` 참조 추가

---

## 완료 기준 (Acceptance Criteria)

- [ ] `/simulate`에서 PM 이름·페르소나 없으면 CTA disabled
- [ ] Submit → `/session/[id]/requirements` (직행 `/session/[id]` 없음)
- [ ] Requirements 화면에서 P0/P1/P2 보드 + 수락/재검토 동작 (mock)
- [ ] Teams 화면에서 10팀 rank desc + 1팀 선택 필수
- [ ] 팀 선택 후 `/session/[id]` — 5 phase stepper + phase별 header 변경
- [ ] 세션·requirements·teams 하단 BackendStatusStrip 동적 갱신
- [ ] PM 채팅 이름 = 사용자 입력 pmPersona.name
- [ ] 리포트에 선택 팀 rank/score + PM 페르소나 + 5단계 요약 표시
- [ ] `NEXT_PUBLIC_MOCK=true` 로 전체 플로우 E2E 동작
