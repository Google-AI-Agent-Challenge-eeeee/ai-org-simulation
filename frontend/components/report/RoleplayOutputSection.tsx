"use client"

import {
  Activity,
  AlertTriangle,
  ChevronDown,
  CheckCircle2,
  FileText,
  Info,
  Layers3,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
} from "lucide-react"
import { motion } from "framer-motion"
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

const STATUS_LABEL: Record<string, string> = {
  good: "양호",
  warning: "주의",
  critical: "위험",
  high: "높음",
  medium: "중간",
  low: "낮음",
}

const SCORE_LABELS: Record<string, { ko: string; hint: string }> = {
  schedule_stability: {
    ko: "일정 안정성",
    hint: "계획한 일정과 마일스톤을 유지할 가능성",
  },
  role_clarity: {
    ko: "역할 명확성",
    hint: "누가 무엇을 책임지는지 명확한 정도",
  },
  technical_risk_control: {
    ko: "기술 리스크 통제",
    hint: "기술 의존성, 미확정 스펙, 구현 리스크를 제어하는 정도",
  },
  integration_readiness: {
    ko: "연동 준비도",
    hint: "FE-BE, API, 외부 시스템 연동을 시작할 준비 정도",
  },
  collaboration_quality: {
    ko: "협업 품질",
    hint: "응답, 합의, 의존성 조율이 원활한 정도",
  },
  qa_release_readiness: {
    ko: "QA/출시 준비도",
    hint: "테스트 커버리지와 릴리즈 체크가 준비된 정도",
  },
  workload_balance: {
    ko: "업무 균형",
    hint: "특정 역할이나 사람에게 일이 몰리지 않은 정도",
  },
}

function badgeClass(value: string) {
  return STATUS_CLASS[value] ?? "text-zinc-300 bg-zinc-800 border-zinc-700"
}

function label(text: string) {
  return text.replace(/_/g, " ")
}

function titleLabel(text: string) {
  return label(text)
    .split(" ")
    .map((word) => {
      const lower = word.toLowerCase()
      if (["api", "be", "fe", "qa"].includes(lower)) return lower.toUpperCase()
      return lower.charAt(0).toUpperCase() + lower.slice(1)
    })
    .join(" ")
}

function scoreLabel(item: ScoreBreakdownItem) {
  return SCORE_LABELS[item.dimension] ?? { ko: label(item.dimension), hint: "시뮬레이션 결과 기반 점수" }
}

function scoreReasons(item: ScoreBreakdownItem) {
  return [
    ...(item.penaltyDetail ?? []).map(formatScoreReason),
    ...(item.phaseSignal ? [formatPhaseSignal(item.phaseSignal)] : []),
    ...((item.deductedBy ?? []).length > 0
      ? [`감점 참조: ${(item.deductedBy ?? []).slice(0, 3).join(", ")}`]
      : []),
  ]
}

function formatScoreReason(reason: string) {
  const match = reason.match(/^(.+)\((.+)\/(.+)\): -(.+)$/)
  if (!match) return reason
  const [, category, status, severity, penalty] = match
  return `${label(category)} 이슈(${status}/${severity})로 ${Number(penalty) * 100}점 감점`
}

function formatPhaseSignal(signal: string) {
  const match = signal.match(/phase_stability_avg=([\d.]+)\s+score\s+([\d.]+)->([\d.]+)/)
  if (!match) return signal
  const [, avg, before, after] = match
  return `관련 phase 안정성 평균 ${Math.round(Number(avg) * 100)}%가 반영되어 ${Math.round(Number(before) * 1000) / 10}점에서 ${Math.round(Number(after) * 1000) / 10}점으로 조정`
}

function evidenceCount(evidenceSummary?: EvidenceSummary) {
  return evidenceSummary?.total_evidence_refs ?? 0
}

function phaseStatLine(phase: PhaseDetail) {
  return `${phase.participantTurns.length} turns · ${phase.detectedIssues.length} issues · ${phase.actionItems.length} actions`
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
        {items.map((item) => {
          const display = scoreLabel(item)
          const reasons = scoreReasons(item)

          return (
            <div key={item.dimension} className="rounded-lg border border-zinc-800/80 bg-zinc-950/35 p-3">
            <div className="mb-1 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-zinc-200">
                  {titleLabel(item.dimension)}
                  {" "}
                  <span className="ml-2 text-xs font-normal text-zinc-500">
                    · {display.ko}
                  </span>
                </p>
                <p className="mt-0.5 text-[11px] leading-relaxed text-zinc-500">
                  {display.hint}
                </p>
              </div>
              <span
                className={cn(
                  "shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-medium",
                  badgeClass(item.status),
                )}
              >
                {STATUS_LABEL[item.status] ?? item.status} · {item.rawScore}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-indigo-500"
                style={{ width: `${Math.max(0, Math.min(100, item.rawScore))}%` }}
              />
            </div>
            {reasons.length > 0 && (
              <details className="group mt-2">
                <summary className="flex cursor-pointer list-none items-center gap-1 text-[11px] font-medium text-zinc-500 hover:text-zinc-300">
                  판단 근거
                  <ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" />
                </summary>
                <div className="mt-2 rounded-md border border-zinc-800 bg-zinc-950/70 p-2">
                  <p className="text-[11px] text-zinc-500">
                    가중치 {item.weight}% · 반영 점수 {item.weightedScore}
                  </p>
                  <ul className="mt-1.5 space-y-1">
                    {reasons.slice(0, 3).map((reason, index) => (
                      <li
                        key={`${item.dimension}-reason-${index}`}
                        className="text-[11px] leading-relaxed text-zinc-400"
                      >
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              </details>
            )}
          </div>
          )
        })}
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
                  <p className="mt-1 text-xs text-zinc-500">
                    {phaseStatLine(phase)}
                  </p>
                </div>
                <span className="rounded-full border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                  {phase.score}
                </span>
              </div>
            </summary>

            <PhaseIntroToggle phase={phase} />

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

function PhaseIntroToggle({ phase }: { phase: PhaseDetail }) {
  return (
    <details className="group/intro mt-4 overflow-hidden rounded-lg border border-cyan-500/15 bg-cyan-500/5">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2">
        <span className="flex items-center gap-2 text-xs font-medium text-cyan-200">
          <Sparkles className="h-3.5 w-3.5" />
          페이즈 소개 보기
        </span>
        <ChevronDown className="h-3.5 w-3.5 text-cyan-200 transition-transform group-open/intro:rotate-180" />
      </summary>

      <div className="grid grid-rows-[0fr] transition-all duration-300 ease-out group-open/intro:grid-rows-[1fr]">
        <div className="overflow-hidden">
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22 }}
            className="border-t border-cyan-500/10 px-3 pb-3 pt-2"
          >
            <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-zinc-300">
                <Info className="h-3.5 w-3.5 text-cyan-300" />
                목적
              </div>
              <p className="text-xs leading-relaxed text-zinc-400">
                {phase.phaseObjective || "No phase objective produced."}
              </p>
              <div className="mt-3 h-px bg-zinc-800" />
              <p className="mt-3 text-xs leading-relaxed text-zinc-500">
                {phase.conversationSummary || "No phase summary produced."}
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </details>
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
