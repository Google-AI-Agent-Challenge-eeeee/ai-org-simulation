/**
 * Mock 시나리오 데이터
 *
 * NEXT_PUBLIC_MOCK=true 시 사용.
 * 페르소나 5명, 대화 20턴, 고정 리포트.
 */

import { ROLE_COLORS } from "../constants"
import type { Message, Persona, Report, SessionStage } from "../types"

export const MOCK_PERSONAS: Persona[] = [
  { id: "p1", name: "김지수", role: "PM", color: ROLE_COLORS.PM, initials: "김지" },
  { id: "p2", name: "이민기", role: "BE", color: ROLE_COLORS.BE, initials: "이민" },
  { id: "p3", name: "박수현", role: "DS", color: ROLE_COLORS.DS, initials: "박수" },
  { id: "p4", name: "최현우", role: "iOS", color: ROLE_COLORS.iOS, initials: "최현" },
  { id: "p5", name: "정민호", role: "QA", color: ROLE_COLORS.QA, initials: "정민" },
]

const [pm, be, ds, ios, qa] = MOCK_PERSONAS

const MOCK_SCRIPT: Array<{ persona: Persona; content: string }> = [
  { persona: pm, content: "안녕하세요! 이번 스프린트 킥오프를 시작하겠습니다. PRD를 검토해 보니 핵심 기능은 로그인/회원가입 API 연동과 메인 대시보드 구현입니다." },
  { persona: be, content: "API 설계는 제가 맡겠습니다. 인증 플로우부터 시작하는 게 좋겠어요. 데이터베이스 스키마 초안은 내일 오전까지 공유드리겠습니다." },
  { persona: ds, content: "디자인 시스템 컴포넌트를 먼저 확정하면 좋겠어요. 특히 다크모드 대응을 위한 컬러 토큰 정의가 시급합니다." },
  { persona: ios, content: "모바일 쪽은 2주 안에 프로토타입 가능합니다. API 문서만 빨리 나오면 바로 연동 작업 들어갈 수 있어요." },
  { persona: qa, content: "QA 리소스 부족이 걱정됩니다. 개발 단계에서부터 E2E 테스트 코드를 병행 작성할 것인지 먼저 결정해 주세요." },
  { persona: pm, content: "좋은 의견 감사합니다. E2E 테스트는 병행 작성으로 진행하겠습니다. 정민호님, 테스트 케이스 설계는 디자인 시안이 나오는 시점부터 시작 부탁드립니다." },
  { persona: be, content: "인증 방식은 JWT + Refresh Token으로 가겠습니다. 소셜 로그인은 2차 스프린트로 미루는 게 현실적일 것 같습니다." },
  { persona: ds, content: "동의합니다. 1차에서는 이메일 로그인에 집중하고, 소셜 로그인은 디자인 패턴만 정의해 두겠습니다." },
  { persona: ios, content: "그럼 iOS 쪽 OAuth 연동은 2차 스프린트 항목으로 옮기겠습니다. 대신 1차에서 오프라인 모드 캐싱을 포함할 수 있을 것 같아요." },
  { persona: qa, content: "오프라인 캐싱이 들어가면 테스트 케이스가 상당히 늘어납니다. 우선순위를 명확히 해주시면 좋겠습니다." },
  { persona: pm, content: "우선순위 정리하겠습니다. P0: 이메일 인증 + 대시보드 기본 뷰. P1: 오프라인 캐싱. P2: 소셜 로그인. 이 방향으로 진행하겠습니다." },
  { persona: be, content: "P0 기준 백엔드 예상 공수는 6일입니다. API 게이트웨이 설정까지 포함한 수치입니다." },
  { persona: ds, content: "디자인은 P0 기준 4일 예상합니다. 컴포넌트 라이브러리 구축과 병행이라 빡빡하긴 한데 가능합니다." },
  { persona: ios, content: "iOS P0 구현은 5일로 보고 있습니다. BE API 의존성이 있어서 2~3일은 병렬 작업으로 진행할 예정입니다." },
  { persona: qa, content: "테스트 계획서 작성 2일, 케이스 실행 3일 잡겠습니다. 총 5일인데 BE 완료 시점과 맞춰야 합니다." },
  { persona: pm, content: "전체 타임라인: D+1 스키마 리뷰, D+3 디자인 시안 리뷰, D+5 BE API 완료, D+7 iOS 연동 완료, D+9 QA 완료, D+10 릴리즈. 동의하시면 진행하겠습니다." },
  { persona: be, content: "백엔드 동의합니다. 다만 D+5 완료를 위해 D+2까지 스키마 확정이 필요합니다." },
  { persona: ds, content: "D+3 시안 리뷰 전에 D+1에 와이어프레임 먼저 공유할게요. 빠른 피드백 부탁드립니다." },
  { persona: ios, content: "일정 동의합니다. Slack 채널에 데일리 진행 상황 공유하겠습니다." },
  { persona: qa, content: "최종 동의합니다. 테스트 환경 세팅은 제가 D+1에 먼저 준비해두겠습니다. 모두 수고 많으셨습니다!" },
]

export const MOCK_REPORT: Report = {
  id: "mock-report-001",
  createdAt: "2026-05-22T19:00:00+09:00",
  team: MOCK_PERSONAS,
  metrics: {
    teamFitScore: 87,
    riskIndex: 23,
    riskLevel: "Low",
    completionRate: 91,
    completionLabel: "Sprint 1",
    riskDistribution: { safe: 70, caution: 20, danger: 10 },
  },
  meetingSummary: {
    decisions: [
      "1차 스프린트는 핵심 로그인/회원가입 API 연동에 집중하기로 합의.",
      "디자인 시스템 컴포넌트 1차 초안 D+1 공유.",
      "소셜 로그인은 2차 스프린트로 이관.",
    ],
    issues: [
      "iOS 파트의 최현우님이 백엔드 API 문서 지연으로 인한 초기 블로킹 우려 제기.",
      "임시 목업 데이터 활용 방안 논의 중.",
    ],
    discussions: [
      "QA 리소스 부족을 해결하기 위해 개발 단계에서부터 E2E 테스트 코드 작성을 병행할 것인지에 대한 비용-편익 논의 진행.",
    ],
  },
  recommendations: [
    {
      type: "burnout",
      title: "번아웃 위험 (디자인)",
      body: "초기 에셋 제작 부하가 높습니다. 디자인 파트 일정을 1주 연장하거나 리소스를 추가 확보하세요.",
    },
    {
      type: "bottleneck",
      title: "병목 가능성 (API 연동)",
      body: "백엔드-프론트엔드 연동 구간에서 병목이 예상됩니다. 일일 스탠드업 미팅을 도입하여 싱크를 맞추세요.",
    },
  ],
}

let sessionCounter = 0

export function startMockSession(): string {
  sessionCounter += 1
  return `mock-session-${sessionCounter}`
}

export function getMockReport(_sessionId: string): Report {
  return MOCK_REPORT
}

export function getMockScript(): Array<{ persona: Persona; content: string }> {
  return MOCK_SCRIPT
}

export type MockSseEvent =
  | { event: "status"; data: { stage: SessionStage; text: string } }
  | { event: "message"; data: { persona: Persona; token: string; messageId: string } }
  | { event: "done"; data: Record<string, never> }

export function buildMockEvents(): MockSseEvent[] {
  const events: MockSseEvent[] = [
    { event: "status", data: { stage: "analyzing", text: "요구사항 분석 중..." } },
    { event: "status", data: { stage: "team_ready", text: "팀 구성 완료 → 킥오프 회의 시작" } },
    { event: "status", data: { stage: "meeting", text: "킥오프 회의 진행 중" } },
  ]

  MOCK_SCRIPT.forEach((line, i) => {
    const messageId = `msg-${i}`
    const words = line.content.split("")
    words.forEach((char) => {
      events.push({
        event: "message",
        data: { persona: line.persona, token: char, messageId },
      })
    })
  })

  events.push({ event: "done", data: {} })
  return events
}

export function buildMockMessages(): Message[] {
  return MOCK_SCRIPT.map((line, i) => ({
    id: `msg-${i}`,
    persona: line.persona,
    content: line.content,
    isStreaming: false,
  }))
}
