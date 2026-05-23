/**
 * Mock 시나리오 데이터
 *
 * NEXT_PUBLIC_MOCK=true 시 사용.
 * 페르소나 5명, 5-phase 대화, 고정 리포트.
 */

import { ROLE_COLORS } from "../constants"
import type {
  Message,
  Persona,
  Report,
  SessionStage,
  SimulationPhase,
  PmPersona,
} from "../types"

// PM은 sessionStore에서 주입 — 기본값 fallback
export function buildMockPersonas(pmPersona?: PmPersona | null): Persona[] {
  return [
    {
      id: "p1",
      name: pmPersona?.name ?? "김지은",
      role: "PM",
      color: ROLE_COLORS.PM,
      initials: pmPersona ? pmPersona.name.slice(0, 2) : "김지",
    },
    { id: "p2", name: "안우빈", role: "BE",  color: ROLE_COLORS.BE,  initials: "안우" },
    { id: "p3", name: "이수호", role: "WEB", color: ROLE_COLORS.WEB, initials: "이수" },
    { id: "p4", name: "최유니", role: "QA",  color: ROLE_COLORS.QA,  initials: "최유" },
    { id: "p5", name: "청우진", role: "Infra", color: ROLE_COLORS.Infra, initials: "청우" },
  ]
}

// Legacy export for compatibility
export const MOCK_PERSONAS: Persona[] = buildMockPersonas()

export function buildMockScript(pmPersona?: PmPersona | null): Array<{
  persona: Persona
  content: string
  turnType?: Message["turnType"]
}> {
  const personas = buildMockPersonas(pmPersona)
  const [pm, be, fe, qa, infra] = personas

  return [
    /* ─── Phase 1: Kickoff ─── */
    {
      persona: pm,
      content: "자, 프로젝트 알파 킥오프를 시작하겠습니다. 주요 목표는 Q3 내에 코어 추천 엔진을 V2로 마이그레이션하는 것입니다. 우선 프론트엔드와 백엔드 간의 API 스택 합의가 필요합니다. 일정상 리스크가 보이는 부분이 있나요?",
      turnType: "initiative",
    },
    {
      persona: be,
      content: "기존 레거시 DB 구조를 그대로 두고 API만 V2로 올리는 건가요? 그렇다면 응답 지연 문제가 해결되지 않을 수 있습니다. 캐싱 레이어 도입이나 DB 마이그레이션이 병행되어야 일정 내 성능 목표를 맞출 수 있을 것 같습니다.",
      turnType: "concern",
    },
    {
      persona: fe,
      content: "프론트엔드 입장에서는 백엔드의 캐싱 구조 확정이 먼저 필요합니다. 데이터 로딩 상태(Loading States) 처리가 달라지기 때문에, 스펙이 늦게 확정되면 UI 작업이 블락될 위험이 있습니다.",
      turnType: "dependency",
    },
    {
      persona: qa,
      content: "QA 환경 세팅도 마이그레이션 전 DB 스냅샷이 필요합니다. 마이그레이션 완료 시점을 D+5로 잡아주시면 테스트 케이스 사전 설계가 가능합니다.",
      turnType: "proposed_action",
    },
    {
      persona: infra,
      content: "Cloud Run 배포 파이프라인은 현재 스테이징 환경에서 검증 중입니다. D+3까지 인프라 확정 가능합니다. GCP IAM 정책 리뷰가 선행되어야 합니다.",
      turnType: "observation",
    },
    /* ─── Phase 2: Design ─── */
    {
      persona: pm,
      content: "설계 단계로 넘어가겠습니다. DB 스키마와 API 명세 작성 일정을 확정합시다. BE 측 초안은 언제 공유 가능한가요?",
      turnType: "initiative",
    },
    {
      persona: be,
      content: "D+2까지 초안 API 스펙 공유 가능합니다. 단 결제 API 연동 파트는 PG사 sandbox 환경이 아직 미개통이라 D+4로 보고 있습니다.",
      turnType: "observation",
    },
    {
      persona: fe,
      content: "API 스펙이 D+2에 나오면 컴포넌트 설계 D+3에 시작 가능합니다. 다만 결제 파트 지연이 D+4라면 해당 UI 작업은 병렬로 진행하면서 목업 데이터로 선개발하겠습니다.",
      turnType: "proposed_action",
    },
    /* ─── Phase 3: Development ─── */
    {
      persona: be,
      content: "D+5 기준 인증 API 완료, D+7 결제 API 완료 예정입니다. 다만 현재 스프린트에 레거시 유지보수 티켓이 3개 추가되어 있어 병목이 우려됩니다.",
      turnType: "concern",
    },
    {
      persona: pm,
      content: "레거시 유지보수 티켓 3개는 다음 스프린트로 이관하겠습니다. 이번 스프린트는 신규 기능에 집중합니다. 안우빈님, 가능한가요?",
      turnType: "proposed_action",
    },
    {
      persona: fe,
      content: "프론트엔드 D+6 기준 로그인 UI 완료, D+9 대시보드 완료 목표입니다. BE API 문서가 D+2에 확정되면 이 일정 지킬 수 있습니다.",
      turnType: "observation",
    },
    /* ─── Phase 4: Integration ─── */
    {
      persona: fe,
      content: "결제 API 연동 시 FE-BE 간 응답 스펙 불일치가 발견됐습니다. error_code 필드 이름이 다릅니다. BE 측 수정 또는 FE 측 adapter 추가 중 어떤 방향이 맞나요?",
      turnType: "concern",
    },
    {
      persona: be,
      content: "BE 측에서 error_code를 errorCode로 통일하겠습니다. 변경 후 API 스펙 문서 업데이트하고 Slack으로 공유하겠습니다.",
      turnType: "proposed_action",
    },
    {
      persona: qa,
      content: "E2E 테스트에서 결제 플로우 성공 케이스는 통과, 실패 케이스 2건 미통과입니다. 재현 환경 공유드리겠습니다.",
      turnType: "observation",
    },
    /* ─── Phase 5: QA/Release ─── */
    {
      persona: qa,
      content: "전체 테스트 커버리지 87% 달성. 릴리즈 블로커 이슈 2건 남아 있습니다. D+13까지 해결 가능 여부 확인 부탁드립니다.",
      turnType: "concern",
    },
    {
      persona: be,
      content: "블로커 이슈 2건 모두 오늘 중 수정 완료 가능합니다. 재배포는 내일 오전 9시 예정입니다.",
      turnType: "proposed_action",
    },
    {
      persona: infra,
      content: "배포 파이프라인 검증 완료, CI/CD 정상 가동 중입니다. 릴리즈 승인 후 바로 진행 가능합니다.",
      turnType: "observation",
    },
    {
      persona: pm,
      content: "수고 많으셨습니다. D+13 수정 완료 후 D+14 릴리즈로 확정하겠습니다. 배포 후 모니터링 담당은 청우진님이 맡아 주세요.",
      turnType: "initiative",
    },
  ]
}

export function buildMockReport(pmPersona?: PmPersona | null): Report {
  return {
    id: "mock-report-001",
    createdAt: new Date().toISOString(),
    team: buildMockPersonas(pmPersona),
    pmPersona: pmPersona ?? undefined,
    selectedTeam: {
      rank: 1,
      teamFitScore: 94.2,
      teamId: "team_001",
      teamName: "알파 포메이션",
    },
    metrics: {
      teamFitScore: 94,
      riskIndex: 12,
      riskLevel: "Low",
      completionRate: 100,
      completionLabel: "Sprint 1",
      confidenceLevel: "High",
      riskDistribution: { technical: 40, resource: 35, timeline: 25 },
    },
    requirementsSummary: {
      acceptedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      bullets: [
        "MVP 스코프 확정: 핵심 기능 4개, 부가 기능 2개 분류 완료",
        "기술 스택 적합도 92%: React + Node.js 아키텍처 제안 승인",
        "예상 공수 산정 완료: 총 12 스프린트 (약 3개월) 소요 예상",
      ],
    },
    meetingSummary: {
      decisions: [
        "인증 API D+5, 결제 API D+7 완료 일정 합의",
        "레거시 유지보수 티켓 3건 다음 스프린트 이관",
        "D+14 릴리즈 확정, 배포 후 모니터링 담당 Infra 배정",
      ],
      issues: [
        "FE-BE 결제 API 응답 스펙 불일치 발견 — error_code 필드명 충돌",
        "PG사 sandbox 미개통으로 결제 파트 D+4 지연",
      ],
      discussions: [
        "캐싱 레이어 도입 vs DB 마이그레이션 비용-편익 논의",
        "QA 커버리지 87% 대 목표 90% 달성 방안 논의",
      ],
    },
    phaseSummaries: [
      { phase: "kickoff",     score: 88, summary: "초기 목표 설정 및 R&R 위할 할당 완료" },
      { phase: "design",      score: 84, summary: "DB 스키마 및 API 명세 작성 합의" },
      { phase: "development", score: 79, summary: "병목 발생 추적, 리소스 재분배 필요" },
      { phase: "integration", score: 82, summary: "자동화 테스트 시나리오 검증 통과" },
      { phase: "qa_release",  score: 91, summary: "CI/CD 파이프라인 정상 가동 확인" },
    ],
    recommendations: [
      {
        type: "bottleneck",
        title: "개발(Dev) 단계 병목 경고",
        body: "시뮬레이션 결과, 개발 단계에서 Dev Lead Agent의 작업 부하가 120%를 초과할 것으로 예상됩니다. 프론트엔드 전문 Agent의 추가 투입을 권장합니다.",
      },
      {
        type: "security",
        title: "보안 컴플라이언스 검토 필요",
        body: "결제 모듈 통합 과정에서 SecOps Agent가 2개의 잠재적 취약점 패턴을 식별했습니다. 배포 전 추가적인 침투 테스트 시뮬레이션이 필요합니다.",
      },
    ],
  }
}

// Kept for backward compat
export const MOCK_REPORT: Report = buildMockReport()

let sessionCounter = 0
export function startMockSession(): string {
  sessionCounter += 1
  return `mock-session-${sessionCounter}`
}
export function getMockReport(_sessionId: string, pmPersona?: PmPersona | null): Report {
  return buildMockReport(pmPersona)
}
export function getMockScript(pmPersona?: PmPersona | null) {
  return buildMockScript(pmPersona)
}

export type MockSseEvent =
  | { event: "status";       data: { stage: SessionStage; text: string; phase?: SimulationPhase; phaseIndex?: number } }
  | { event: "message";      data: { persona: Persona; token: string; messageId: string; turnType?: Message["turnType"] } }
  | { event: "backend_log";  data: { text: string } }
  | { event: "event_start";  data: { eventId: string; description: string } }
  | { event: "event_end";    data: { eventId: string } }
  | { event: "done";         data: Record<string, never> }

export function buildMockEvents(pmPersona?: PmPersona | null): MockSseEvent[] {
  const events: MockSseEvent[] = []
  const script = buildMockScript(pmPersona)

  const PHASE_LOGS: string[][] = [
    [
      "Simulation_Input_Packet 병합 중…",
      "PrivacyColumnFilter · PII 컬럼 제거 완료",
      "AgentCardBuilder · 5명 Agent Card 생성",
      "ScenarioPhasePlanner · 리스크 기반 시나리오 13개 배치",
    ],
    [
      "Orchestrator · Phase 2/5 Design Phase 시작",
      "RoleAgent · BE 안우빈 observation 생성",
    ],
    [
      "Orchestrator · Phase 3/5 Development Phase 시작",
      "RoleAgent · PM proposed_action 생성",
    ],
    [
      "Orchestrator · Phase 4/5 Integration Phase 시작",
      "PhaseLogCollector · 이슈 4건, 결정 3건 집계",
    ],
    [
      "Orchestrator · Phase 5/5 QA/Release Phase 시작",
      "PhaseLogCollector · 최종 Phase Log 저장 완료",
      "ScoreCalculator · 팀 안정성 점수 계산 중…",
    ],
  ]

  const PHASE_NAMES: SimulationPhase[] = [
    "kickoff", "design", "development", "integration", "qa_release",
  ]
  const PHASE_LABELS = [
    "킥오프 회의 진행 중…",
    "설계 단계 진행 중…",
    "개발 단계 진행 중…",
    "연동 단계 진행 중…",
    "QA/릴리즈 진행 중…",
  ]

  // phase turn boundaries (script indices)
  const phaseBoundaries = [0, 5, 8, 11, 14]

  // 각 phase 내 이벤트 분할 (예: [0,2], [2,5] 등)
  const MOCK_EVENTS = [
    { id: "evt_k1", desc: "킥오프: 프로젝트 목표 및 일정 공유", start: 0, end: 2 },
    { id: "evt_k2", desc: "킥오프: 역할 및 책임 배분 확인",    start: 2, end: 5 },
    { id: "evt_d1", desc: "설계: API 스펙 및 DB 스키마 논의",   start: 5, end: 8 },
    { id: "evt_v1", desc: "개발: 업무 배분 및 일정 리스크 확인", start: 8, end: 11 },
    { id: "evt_i1", desc: "연동: FE/BE 연동 스펙 점검",         start: 11, end: 14 },
    { id: "evt_q1", desc: "QA/릴리즈: 테스트 커버리지 및 릴리즈 블로커 확인", start: 14, end: script.length },
  ]

  events.push({ event: "status", data: { stage: "meeting", text: PHASE_LABELS[0], phase: "kickoff", phaseIndex: 1 } })
  PHASE_LOGS[0].forEach((log) => {
    events.push({ event: "backend_log", data: { text: log } })
  })

  script.forEach((line, i) => {
    // Phase transition
    if (phaseBoundaries.slice(1).includes(i)) {
      const pi = phaseBoundaries.indexOf(i)
      events.push({
        event: "status",
        data: { stage: "meeting", text: PHASE_LABELS[pi], phase: PHASE_NAMES[pi], phaseIndex: pi + 1 },
      })
      PHASE_LOGS[pi]?.forEach((log) => {
        events.push({ event: "backend_log", data: { text: log } })
      })
    }

    // 이벤트 시작 마커
    const startEvt = MOCK_EVENTS.find((e) => e.start === i)
    if (startEvt) {
      events.push({ event: "event_start", data: { eventId: startEvt.id, description: startEvt.desc } })
    }

    const messageId = `msg-${i}`
    const chars = line.content.split("")
    chars.forEach((char) => {
      events.push({
        event: "message",
        data: { persona: line.persona, token: char, messageId, turnType: line.turnType },
      })
    })

    // 이벤트 종료 마커
    const endEvt = MOCK_EVENTS.find((e) => e.end - 1 === i)
    if (endEvt) {
      events.push({ event: "event_end", data: { eventId: endEvt.id } })
    }
  })

  events.push({ event: "backend_log", data: { text: "리포트 생성 완료 · PhaseLogCollector" } })
  events.push({ event: "done", data: {} })

  return events
}
