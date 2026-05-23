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

export interface ReportSummary {
  projectName: string
  verdict: string
  scoreNote: string
  generatedFrom: string[]
  outputCoverage: {
    phaseCount: number
    topRiskCount: number
    mustFixCount: number
    scoreDimensionCount: number
  }
}

export interface ScoreBreakdownItem {
  dimension: string
  rawScore: number
  weightedScore: number
  weight: number
  status: string
  deductedBy?: string[]
  penaltyDetail?: string[]
  phaseSignal?: string
}

export interface ReportRisk {
  rank?: number
  issueCategory: string
  severity: string
  status: string
  observedInPhases: string[]
  suggestedAction: string
  evidenceRefs: string[]
  rootCause?: string
  finalIssueScore?: number
}

export interface MustFixItem {
  issueCategory: string
  severity: string
  suggestedAction: string
  affectedRoles: string[]
}

export interface EvidenceSummary {
  total_evidence_refs?: number
  total_confirmed_issues?: number
  total_candidate_issues?: number
  total_unresolved_turns?: number
  phases_with_high_risk?: string[]
}

export interface PhaseDetail {
  phase: SimulationPhase
  phaseName: string
  phaseObjective: string
  conversationSummary: string
  score: number
  triggerSources: string[]
  participantTurns: Array<{
    agentId: string
    role: string
    observation: string
    concern: string
    dependency: string
    proposedAction: string
    evidenceRefsUsed: string[]
    isValid: boolean
  }>
  detectedIssues: Array<{
    issueId: string
    issueCategory: string
    description: string
    raisedBy: string
    severity: string
    status: string
    evidenceRefs: string[]
  }>
  decisions: Array<{ id: string; text: string; phase: string }>
  actionItems: Array<{
    actionId: string
    description: string
    ownerRole: string
    priority: string
    evidenceRefs: string[]
  }>
  unresolvedQuestions: Array<{ id: string; text: string; phase: string }>
}

export interface IssueSummary {
  confirmedCount: number
  candidateCount: number
  invalidCount: number
  confirmedIssues: ReportRisk[]
  candidateIssues: ReportRisk[]
  invalidIssues: ReportRisk[]
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
  reportSummary?: ReportSummary
  scoreBreakdown?: ScoreBreakdownItem[]
  topRisks?: ReportRisk[]
  mustFixBeforeStart?: MustFixItem[]
  evidenceSummary?: EvidenceSummary
  phaseDetails?: PhaseDetail[]
  issueSummary?: IssueSummary
}

export interface SimulationInput {
  prd: string
  pmPersona: PmPersona
  pmPriority: string
}
