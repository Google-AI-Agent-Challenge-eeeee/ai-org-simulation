import type { RoleType, SessionStage, SimulationPhase } from "./types"

export const ROLE_COLORS: Record<RoleType, string> = {
  PM: "bg-purple-500",
  BE: "bg-blue-600",
  WEB: "bg-cyan-500",
  iOS: "bg-slate-500",
  Android: "bg-green-600",
  Infra: "bg-orange-500",
  QA: "bg-amber-600",
  DS: "bg-pink-500",
}

export const ROLE_LABELS: Record<RoleType, string> = {
  PM: "PM",
  BE: "Backend",
  WEB: "Frontend",
  iOS: "iOS",
  Android: "Android",
  Infra: "Infra",
  QA: "QA",
  DS: "Design",
}

export const STAGE_STATUS_TEXT: Record<SessionStage, string> = {
  idle: "",
  analyzing: "요구사항 분석 중...",
  requirements_review: "요구사항 검토 대기 중",
  team_selection: "팀 매칭 중...",
  team_ready: "팀 구성 완료 → 시뮬레이션 시작",
  meeting: "시뮬레이션 진행 중",
  done: "시뮬레이션 완료 → 리포트 생성 중",
}

export const PM_STYLE_PRESETS = [
  { id: "speed",   label: "속도 우선" },
  { id: "quality", label: "품질 우선" },
  { id: "balance", label: "균형" },
  { id: "custom",  label: "직접 입력" },
] as const

export type PmStylePreset = (typeof PM_STYLE_PRESETS)[number]["id"]

export const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

/* ─── Simulation Phase Meta ─────────────── */

export const PHASE_META: Record<
  SimulationPhase,
  { label: string; subtitle: string; icon: string }
> = {
  kickoff:     { label: "Kickoff",     subtitle: "목표·R&R·일정 합의",        icon: "🚀" },
  design:      { label: "Design",      subtitle: "API/DB 스펙·기술 선택",      icon: "⚙️" },
  development: { label: "Development", subtitle: "구현·PR·병목 대응",           icon: "💻" },
  integration: { label: "Integration", subtitle: "FE-BE 연동·스펙 싱크",       icon: "🔗" },
  qa_release:  { label: "QA/Release",  subtitle: "테스트·배포·릴리즈 검증",    icon: "🚢" },
}

export const PHASE_ORDER: SimulationPhase[] = [
  "kickoff",
  "design",
  "development",
  "integration",
  "qa_release",
]

/* ─── Backend Log Templates ─────────────── */

export const REQUIREMENTS_BACKEND_LOGS = [
  "Requirements_Agent: PRD 파싱 완료",
  "역할·기술 스택 추출 중…",
  "기능 우선순위(P0/P1/P2) 분류 완료",
  "PM 페르소나 프롬프트 주입 완료",
]

export const TEAMS_BACKEND_LOGS = [
  "직원 적합도 DB 비교 중…",
  "팀 조합 경우의 수 계산: 1,247 combinations",
  "스코어 정렬 완료 — 상위 10팀 추출",
  "대기 중 — PM 팀 선택 필요",
]

export const SESSION_BACKEND_LOGS = [
  "Simulation_Input_Packet 병합 중…",
  "PrivacyColumnFilter · PII 컬럼 제거 완료",
  "AgentCardBuilder · 5명 Agent Card 생성",
  "ScenarioPhasePlanner · 리스크 기반 시나리오 13개 배치",
  "Orchestrator · evt_001 backend_workload_concentration 처리 중",
  "RoleAgent · BE 안우빈 observation 생성",
  "Phase 2/5 Design Phase 시작",
  "PhaseLogCollector · 이슈 4건, 결정 3건 집계",
]
