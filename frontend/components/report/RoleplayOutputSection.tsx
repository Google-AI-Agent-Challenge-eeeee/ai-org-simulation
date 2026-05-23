import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Layers3,
  MessageSquareText,
  ShieldCheck,
} from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { cn } from "@/lib/utils"
import type {
  EvidenceSummary,
  MustFixItem,
  PhaseDetail,
  ReportRisk,
  ReportSummary,
  ScoreBreakdownItem,
} from "@/lib/types"

interface RoleplayOutputSectionProps {
  reportSummary?: ReportSummary
  scoreBreakdown?: ScoreBreakdownItem[]
  topRisks?: ReportRisk[]
  mustFixBeforeStart?: MustFixItem[]
  evidenceSummary?: EvidenceSummary
  phaseDetails?: PhaseDetail[]
}

const STATUS_CLASS: Record<string, string> = {
  good: "text-emerald-300 bg-emerald-500/10 border-emerald-500/25",
  warning: "text-amber-300 bg-amber-500/10 border-amber-500/25",
  critical: "text-red-300 bg-red-500/10 border-red-500/25",
  high: "text-red-300 bg-red-500/10 border-red-500/25",
  medium: "text-amber-300 bg-amber-500/10 border-amber-500/25",
  low: "text-emerald-300 bg-emerald-500/10 border-emerald-500/25",
}

function badgeClass(value: string) {
  return STATUS_CLASS[value] ?? "text-zinc-300 bg-zinc-800 border-zinc-700"
}

function label(text: string) {
  return text.replace(/_/g, " ")
}

function evidenceCount(evidenceSummary?: EvidenceSummary) {
  return evidenceSummary?.total_evidence_refs ?? 0
}

export function RoleplayOutputSection({
  reportSummary,
  scoreBreakdown = [],
  topRisks = [],
  mustFixBeforeStart = [],
  evidenceSummary,
  phaseDetails = [],
}: RoleplayOutputSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 print-section">
      <SectionHeader icon={FileText} title="Roleplay Output Report" />

      {reportSummary && (
        <div className="grid gap-3 md:grid-cols-[1.5fr_1fr]">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Project verdict</p>
            <h2 className="mt-1 text-lg font-semibold text-zinc-100">
              {label(reportSummary.verdict)}
            </h2>
            {reportSummary.scoreNote && (
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                {reportSummary.scoreNote}
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2">
            <OutputMetric label="Phases" value={reportSummary.outputCoverage.phaseCount} />
            <OutputMetric label="Risks" value={reportSummary.outputCoverage.topRiskCount} />
            <OutputMetric label="Must fix" value={reportSummary.outputCoverage.mustFixCount} />
            <OutputMetric label="Evidence" value={evidenceCount(evidenceSummary)} />
          </div>
        </div>
      )}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <ScorePanel items={scoreBreakdown} />
        <RiskPanel risks={topRisks} mustFix={mustFixBeforeStart} />
      </div>

      <PhasePanel phases={phaseDetails} />
    </div>
  )
}

function OutputMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
      <p className="text-[11px] text-zinc-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-zinc-100">{value}</p>
    </div>
  )
}

function ScorePanel({ items }: { items: ScoreBreakdownItem[] }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Activity className="h-4 w-4 text-indigo-300" />
        <h3 className="text-sm font-semibold text-zinc-100">Score Breakdown</h3>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.dimension}>
            <div className="mb-1 flex items-center justify-between gap-3">
              <span className="text-sm text-zinc-300">{label(item.dimension)}</span>
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[11px] font-medium",
                  badgeClass(item.status),
                )}
              >
                {item.rawScore}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-indigo-500"
                style={{ width: `${Math.max(0, Math.min(100, item.rawScore))}%` }}
              />
            </div>
            {item.penaltyDetail && item.penaltyDetail.length > 0 && (
              <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
                {item.penaltyDetail.slice(0, 2).join(" / ")}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function RiskPanel({
  risks,
  mustFix,
}: {
  risks: ReportRisk[]
  mustFix: MustFixItem[]
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-300" />
        <h3 className="text-sm font-semibold text-zinc-100">Risk and Actions</h3>
      </div>

      <div className="space-y-3">
        {risks.slice(0, 5).map((risk) => (
          <div key={`${risk.rank}-${risk.issueCategory}`} className="border-b border-zinc-800 pb-3 last:border-b-0 last:pb-0">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-zinc-100">{label(risk.issueCategory)}</p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-500">
                  {risk.suggestedAction}
                </p>
              </div>
              <span
                className={cn(
                  "shrink-0 rounded-full border px-2 py-0.5 text-[11px]",
                  badgeClass(risk.severity),
                )}
              >
                {risk.severity}
              </span>
            </div>
            {risk.observedInPhases.length > 0 && (
              <p className="mt-1 text-[11px] text-zinc-600">
                {risk.observedInPhases.join(", ")}
              </p>
            )}
          </div>
        ))}
      </div>

      {mustFix.length > 0 && (
        <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/5 p-3">
          <div className="mb-2 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-red-300" />
            <p className="text-xs font-semibold text-red-200">Must fix before start</p>
          </div>
          <ul className="space-y-1">
            {mustFix.map((item) => (
              <li key={item.issueCategory} className="text-xs leading-relaxed text-zinc-400">
                {label(item.issueCategory)}: {item.suggestedAction}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function PhasePanel({ phases }: { phases: PhaseDetail[] }) {
  if (phases.length === 0) return null

  return (
    <div className="mt-5">
      <div className="mb-3 flex items-center gap-2">
        <Layers3 className="h-4 w-4 text-cyan-300" />
        <h3 className="text-sm font-semibold text-zinc-100">Phase Logs</h3>
      </div>

      <div className="space-y-3">
        {phases.map((phase) => (
          <details
            key={phase.phaseName}
            className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4 print-open"
            open
          >
            <summary className="cursor-pointer list-none">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-zinc-100">{phase.phaseName}</p>
                  <p className="mt-1 text-xs leading-relaxed text-zinc-500">
                    {phase.conversationSummary || phase.phaseObjective}
                  </p>
                </div>
                <span className="rounded-full border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                  {phase.score}
                </span>
              </div>
            </summary>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <PhaseList
                icon={CheckCircle2}
                title="Decisions"
                items={phase.decisions.map((item) => item.text)}
              />
              <PhaseList
                icon={AlertTriangle}
                title="Detected issues"
                items={phase.detectedIssues.map((item) => item.description)}
              />
              <PhaseList
                icon={MessageSquareText}
                title="Agent turns"
                items={phase.participantTurns.map(
                  (turn) => `${turn.role}: ${turn.concern || turn.observation}`,
                )}
              />
              <PhaseList
                icon={Activity}
                title="Action items"
                items={phase.actionItems.map((item) => item.description)}
              />
            </div>
          </details>
        ))}
      </div>
    </div>
  )
}

function PhaseList({
  icon: Icon,
  title,
  items,
}: {
  icon: typeof Activity
  title: string
  items: string[]
}) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5">
        <Icon className="h-3.5 w-3.5 text-zinc-500" />
        <p className="text-xs font-semibold text-zinc-300">{title}</p>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="text-xs leading-relaxed text-zinc-500">
            {item}
          </li>
        ))}
        {items.length === 0 && (
          <li className="text-xs text-zinc-600">No item produced.</li>
        )}
      </ul>
    </div>
  )
}
