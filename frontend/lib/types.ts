export type RoleType =
  | "PM"
  | "BE"
  | "WEB"
  | "iOS"
  | "Android"
  | "Infra"
  | "QA"
  | "DS"

export interface Persona {
  id: string
  name: string
  role: RoleType
  /** Tailwind bg-* class — e.g. "bg-purple-500" */
  color: string
  /** 2자 이니셜 — e.g. "김지" */
  initials: string
}

export interface Message {
  id: string
  persona: Persona
  content: string
  isStreaming: boolean
}

export type SessionStage =
  | "idle"
  | "analyzing"
  | "team_ready"
  | "meeting"
  | "done"

export interface SessionState {
  sessionId: string | null
  stage: SessionStage
  statusText: string
  messages: Message[]
  elapsed: number
}

export interface ReportMetrics {
  teamFitScore: number
  riskIndex: number
  riskLevel: "Low" | "Mid" | "High"
  completionRate: number
  completionLabel: string
  riskDistribution: {
    safe: number
    caution: number
    danger: number
  }
}

export interface MeetingSummaryData {
  decisions: string[]
  issues: string[]
  discussions: string[]
}

export type RecommendationType = "burnout" | "bottleneck" | "turnover"

export interface Recommendation {
  type: RecommendationType
  title: string
  body: string
}

export interface Report {
  id: string
  createdAt: string
  team: Persona[]
  metrics: ReportMetrics
  meetingSummary: MeetingSummaryData
  recommendations: Recommendation[]
}

export interface SimulationInput {
  prd: string
  pmStyle: string
}
