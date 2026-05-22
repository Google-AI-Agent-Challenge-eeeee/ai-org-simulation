# Frontend 구현 문서

## 개요

사용자가 웹에서 직접 보는 화면 3개를 구현합니다.
백엔드 파이프라인(Requirements_Agent → Compare → Shadow Role Play → Report_Agent)은 숨김 처리되고,
사용자에게는 입력 → 킥오프 회의 관람 → 리포트 열람만 노출됩니다.

---

## 화면 구성

```
/ (입력)  →  /session/[id] (킥오프 회의)  →  /report/[id] (최종 리포트)
```

### 화면 1: 입력 (`/`)
- PRD 텍스트 직접 입력 또는 .md/.txt 파일 업로드 (탭 전환)
- PM 요구사항 프리셋 칩 (속도 우선 / 품질 우선 / 균형 / 직접 입력) + 자유 텍스트
- "시뮬레이션 시작" 버튼 → POST /api/sessions → /session/[id] 이동

### 화면 2: 킥오프 회의 (`/session/[id]`)
- 상태 배너: 파이프라인 단계 한 줄 표시 + 경과 타이머
- 페르소나 그룹챗: 역할별 고유 색상/아바타로 대화 실시간 스트리밍 (SSE)
- 완료 후 "리포트 보기" 버튼 활성화 → /report/[id]

### 화면 3: 최종 리포트 (`/report/[id]`)
- 구성 팀 아바타 칩
- 수치 평가 (팀 핏 점수 / 리스크 지수 / 예상 완료율 / 리스크 분포 바)
- 킥오프 회의 요약 (합의된 결정사항 / 발생한 이슈 / 주요 논의 포인트)
- 권고 사항 (번아웃/병목/이직 리스크 경고 + 행동 제안)
- JSON 다운로드 / 링크 복사

---

## 기술 스택

| 항목 | 선택 | 이유 |
|------|------|------|
| Framework | Next.js 15 (App Router) | README 기존 구조 (`pnpm --filter frontend dev`) |
| Styling | Tailwind CSS v4 + shadcn/ui | 빠른 다크 테마 구현 |
| 상태관리 | Zustand | 가볍고 SSR 친화적 |
| 스트리밍 | SSE (Server-Sent Events) | FastAPI StreamingResponse 연동 |
| 패키지 | pnpm (workspace 준수) | 기존 `pnpm-workspace.yaml` |

---

## 컴포넌트 구조 (Atomic Design)

```
Atoms (components/ui/)
  Avatar, RoleBadge, PresetChip, SectionHeader, MetricCard

Molecules
  components/input/    TabGroup, PrdTextarea(shadcn), FileDropzone, PresetChipGroup
  components/session/  PersonaAvatar, MessageBubble, TypingDots
  components/report/   PersonaChip, RiskDistributionBar, SummaryItem, RecommendationCard

Organisms
  components/input/    PrdInputCard, PmStyleCard
  components/session/  SessionHeader, StatusBar, PersonaMessage, MeetingChat
  components/report/   TeamSection, MetricsSection, MeetingSummarySection, RecommendationSection
  components/layout/   AppHeader, SessionFooter

Pages (app/)
  page.tsx             화면 1 — Organism 조립만, 로직은 useInputForm()
  session/[id]/page.tsx 화면 2 — Organism 조립만, 로직은 useKickoff()
  report/[id]/page.tsx  화면 3 — Organism 조립만, 로직은 useReport()
```

### 클린 코드 원칙

| 원칙 | 적용 방식 |
|------|----------|
| 단일 책임 | 컴포넌트는 렌더링만, 로직은 hook으로 분리 |
| Page는 조립만 | Page 파일에 비즈니스 로직 금지 |
| Props 최소화 | 복잡한 데이터는 타입 객체 통째로 전달 |
| Mock 완전 격리 | `lib/api.ts` 내에서만 NEXT_PUBLIC_MOCK 분기 |

---

## 상태 흐름

```
useInputForm()
  └─ createSession() → sessionStore.setSessionId()
       └─ router.push(/session/[id])

useKickoff(sessionId)   — /session/[id] 마운트 시 실행
  └─ SSE 수신
       ├─ event: status  → sessionStore.setStage()
       ├─ event: message → sessionStore.appendMessage() / appendToken()
       └─ event: done    → router.push(/report/[id])

useReport(sessionId)    — /report/[id] 마운트 시 실행
  └─ fetchReport() → local state (report, loading, error)
```

---

## 백엔드 API 연동 (3개)

| Method | Path | 방식 | 역할 |
|--------|------|------|------|
| `POST` | `/api/sessions` | JSON | 세션 생성 → `session_id` 반환 |
| `GET`  | `/api/sessions/{id}/stream` | SSE | 킥오프 회의 스트리밍 |
| `GET`  | `/api/sessions/{id}/report` | JSON | 최종 리포트 조회 |

### SSE 이벤트 구조

```
event: status   → { stage: "analyzing" | "team_ready" | "meeting" | "done", text: string }
event: message  → { persona: Persona, token: string, messageId: string }
event: done     → {}
```

---

## Mock 모드

`NEXT_PUBLIC_MOCK=true` (.env.local) 설정 시:
- `lib/mock/scenario.ts`에서 하드코딩 데이터 사용
- 페르소나 5명 (PM/BE/DS/iOS/QA), 대화 20턴
- 30ms 간격으로 토큰 emit (실제 스트리밍 체감)
- 완료 후 고정 리포트 데이터 반환

---

## 개발 실행

```bash
# frontend 디렉토리에서
pnpm dev

# 또는 workspace root에서
pnpm --filter frontend dev
```

환경변수 (`frontend/.env.local`):
```
NEXT_PUBLIC_MOCK=true          # 백엔드 없이 Mock 모드로 실행
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 브랜치 / 커밋 컨벤션

README 컨벤션 준수:

```
브랜치: front/feat/chatbot-ui
커밋:   front/feat: <summary>
        front/fix: <summary>
        front/update: <summary>
```
