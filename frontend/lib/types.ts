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
  /** Tailwind bg-* class */
  color: string
  initials: string
}

export interface PmPersona {
  name: string
  preset: import("./constants").PmStylePreset
  persona: string
  constraints?: string
}

export interface Message {
  id: string
  persona: Persona
  content: string
  isStreaming: boolean
  turnType?: "observation" | "concern" | "dependency" | "proposed_action" | "initiative"
  /** 이벤트 구분 마커 - "chat"(default) | "event_start" | "event_end" */
  kind?: "chat" | "event_start" | "event_end"
  /** event_start / event_end 마커일 때 이벤트 설명 */
  eventDescription?: string
  /** event_start / event_end 마커를 연결하는 ID */
  eventId?: string
}

export type SessionStage =
  | "idle"
  | "analyzing"
  | "requirements_review"
  | "team_selection"
  | "team_ready"
  | "meeting"
  | "done"

export type SimulationPhase =
  | "kickoff"
  | "design"
  | "development"
  | "integration"
  | "qa_release"

export interface SessionState {
  sessionId: string | null
  stage: SessionStage
  statusText: string
  messages: Message[]
  elapsed: number
}

/* ─── Requirements ─────────────────────── */

export interface Feature {
  feature_id: string
  feature_name: string
  priority: "P0" | "P1" | "P2"
  assigned_role: string
  estimated_days: number
  dependencies?: string[]
  risk_notes?: string
}

export interface Milestone {
  label: string
  day: number
}

export interface RequirementsSummary {
  project_name: string
  project_summary: string
  required_roles: string[]
  required_skills: string[]
  features: Feature[]
  timeline_days: number
  milestones: Milestone[]
  risk_flags: string[]
  confidence: number
}

/* ─── Teams ────────────────────────────── */

export interface TeamMember {
  employee_id: string
  employee_name: string
  assigned_role: string
  initials: string
  color: string
}

export interface TeamCandidate {
  team_id: string
  team_name: string
  team_rank: number
  team_fit_score: number
  role_coverage_score: number
  skill_coverage_score: number
  availability_score: number
  team_risk_flags: string[]
  members: TeamMember[]
  rationale?: string
  skill_gaps?: string[]
  badges?: string[]
}

/* ─── Report ───────────────────────────── */

export interface ReportMetrics {
  teamFitScore: number
  riskIndex: number
  riskLevel: "Low" | "Mid" | "High"
  completionRate: number
  completionLabel: string
  riskDistribution: {
    technical: number
    resource: number
    timeline: number
  }
  confidenceLevel?: "Low" | "Mid" | "High"
}

export interface MeetingSummaryData {
  decisions: string[]
  issues: string[]
  discussions: string[]
}

export interface PhaseSummary {
  phase: SimulationPhase
  score: number
  summary: string
}

export type RecommendationType = "burnout" | "bottleneck" | "turnover" | "security"

export interface Recommendation {
  type: RecommendationType
  title: string
  body: string
}

export interface RequirementsAcceptedSummary {
  acceptedAt: string
  bullets: string[]
}

export interface Report {
  id: string
  createdAt: string
  team: Persona[]
  metrics: ReportMetrics
  meetingSummary: MeetingSummaryData
  recommendations: Recommendation[]
  pmPersona?: PmPersona
  selectedTeam?: {
    rank: number
    teamFitScore: number
    teamId: string
    teamName: string
  }
  requirementsSummary?: RequirementsAcceptedSummary
  phaseSummaries?: PhaseSummary[]
}

export interface SimulationInput {
  prd: string
  pmPersona: PmPersona
  pmPriority: string
}
