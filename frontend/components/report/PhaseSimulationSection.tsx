import {
  Code2,
  GitMerge,
  Rocket,
  ShieldCheck,
  TrendingUp,
  Waypoints,
  type LucideIcon,
} from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { PHASE_META } from "@/lib/constants"
import { cn } from "@/lib/utils"
import type { PhaseSummary, SimulationPhase } from "@/lib/types"

interface PhaseSimulationSectionProps {
  phaseSummaries: PhaseSummary[]
  footerNote?: string
}

const PHASE_STYLE: Record<
  SimulationPhase,
  { icon: LucideIcon; accent: string; glow: string; label: string }
> = {
  kickoff: {
    icon: Rocket,
    accent: "border-indigo-400/35 bg-indigo-500/10 text-indigo-200",
    glow: "bg-indigo-400",
    label: "Kickoff",
  },
  design: {
    icon: Waypoints,
    accent: "border-violet-400/35 bg-violet-500/10 text-violet-200",
    glow: "bg-violet-400",
    label: "Design",
  },
  development: {
    icon: Code2,
    accent: "border-sky-400/35 bg-sky-500/10 text-sky-200",
    glow: "bg-sky-400",
    label: "Development",
  },
  integration: {
    icon: GitMerge,
    accent: "border-amber-400/35 bg-amber-500/10 text-amber-200",
    glow: "bg-amber-400",
    label: "Integration",
  },
  qa_release: {
    icon: ShieldCheck,
    accent: "border-emerald-400/35 bg-emerald-500/10 text-emerald-200",
    glow: "bg-emerald-400",
    label: "QA / Release",
  },
}

function phaseLabel(phase: SimulationPhase) {
  return PHASE_META[phase]?.label || PHASE_STYLE[phase].label
}

function scoreColor(score: number) {
  if (score >= 85) return "text-emerald-400"
  if (score >= 70) return "text-amber-400"
  if (score >= 45) return "text-rose-400"
  return "text-red-400"
}

function scoreTrackColor(score: number) {
  if (score >= 85) return "bg-emerald-400"
  if (score >= 70) return "bg-amber-400"
  if (score >= 45) return "bg-rose-400"
  return "bg-red-500"
}

function scoreBadgeClass(score: number) {
  if (score >= 85) return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
  if (score >= 70) return "border-amber-500/30 bg-amber-500/10 text-amber-200"
  if (score >= 45) return "border-rose-500/30 bg-rose-500/10 text-rose-200"
  return "border-red-500/30 bg-red-500/10 text-red-200"
}

export function PhaseSimulationSection({
  phaseSummaries,
  footerNote,
}: PhaseSimulationSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 print-section">
      <SectionHeader icon={TrendingUp} title="5단계 시뮬레이션 요약" />

      <div className="relative overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-5">
        <div className="absolute left-8 right-8 top-[3.15rem] h-px bg-zinc-700" />

        <div className="grid grid-cols-5 gap-2">
          {phaseSummaries.map((phase) => {
            const style = PHASE_STYLE[phase.phase]
            const Icon = style.icon

            return (
              <div
                key={phase.phase}
                className="relative flex min-w-0 flex-col items-center gap-2 text-center"
              >
                <div
                  className={cn(
                    "relative z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border shadow-lg",
                    style.accent,
                  )}
                >
                  <span
                    className={cn(
                      "absolute inset-1 rounded-full opacity-15 blur-md",
                      style.glow,
                    )}
                  />
                  <Icon className="relative h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-[10px] font-medium uppercase tracking-wide text-zinc-500 sm:text-[11px]">
                    {phaseLabel(phase.phase)}
                  </p>
                  <p
                    className={cn(
                      "mt-0.5 text-lg font-semibold tabular-nums",
                      scoreColor(phase.score),
                    )}
                  >
                    {phase.score}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {phaseSummaries.map((phase) => {
          const style = PHASE_STYLE[phase.phase]

          return (
            <article
              key={phase.phase}
              className="rounded-lg border border-zinc-800 bg-zinc-950/35 p-3"
            >
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2">
                  <span className={cn("h-2 w-2 shrink-0 rounded-full", style.glow)} />
                  <h3 className="truncate text-sm font-medium text-zinc-100">
                    {phaseLabel(phase.phase)}
                  </h3>
                </div>
                <span
                  className={cn(
                    "shrink-0 rounded-full border px-2 py-0.5 text-xs font-semibold tabular-nums",
                    scoreBadgeClass(phase.score),
                  )}
                >
                  {phase.score}
                </span>
              </div>
              <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-zinc-800">
                <div
                  className={cn("h-full rounded-full", scoreTrackColor(phase.score))}
                  style={{ width: `${Math.max(4, Math.min(100, phase.score))}%` }}
                />
              </div>
              <p className="text-xs leading-relaxed text-zinc-400">{phase.summary}</p>
            </article>
          )
        })}
      </div>

      {footerNote && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-indigo-500/15 bg-indigo-500/5 px-3 py-2 text-xs text-zinc-400">
          <span className="h-2 w-2 shrink-0 rounded-full bg-indigo-400" />
          <span>{footerNote}</span>
        </div>
      )}
    </div>
  )
}
