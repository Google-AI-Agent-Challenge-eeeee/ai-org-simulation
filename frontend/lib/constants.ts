import type { RoleType, SessionStage } from "./types"

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
  team_ready: "팀 구성 완료 → 킥오프 회의 시작",
  meeting: "킥오프 회의 진행 중",
  done: "회의 완료 → 리포트 생성 중",
}

export const PM_STYLE_PRESETS = [
  { id: "speed", label: "속도 우선" },
  { id: "quality", label: "품질 우선" },
  { id: "balance", label: "균형" },
  { id: "custom", label: "직접 입력" },
] as const

export type PmStylePreset = (typeof PM_STYLE_PRESETS)[number]["id"]

export const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
