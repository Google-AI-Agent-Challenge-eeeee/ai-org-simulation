import { TrendingUp } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { PHASE_META } from "@/lib/constants"
import { cn } from "@/lib/utils"
import type { PhaseSummary } from "@/lib/types"

interface PhaseSimulationSectionProps {
  phaseSummaries: PhaseSummary[]
  footerNote?: string
}

function scoreColor(score: number) {
  if (score >= 85) return "text-emerald-400"
  if (score >= 70) return "text-amber-400"
  return "text-red-400"
}

export function PhaseSimulationSection({
  phaseSummaries,
  footerNote,
}: PhaseSimulationSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={TrendingUp} title="5단계 시뮬레이션 요약" />

      <div className="flex items-start gap-0 relative">
        {/* connecting line */}
        <div className="absolute top-5 left-5 right-5 h-px bg-zinc-700 z-0" />

        {phaseSummaries.map((ps, i) => {
          const meta = PHASE_META[ps.phase]
          return (
            <div key={ps.phase} className="relative z-10 flex flex-col items-center flex-1 min-w-0">
              {/* icon circle */}
              <div className="w-10 h-10 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-lg mb-2 shrink-0">
                {meta.icon}
              </div>
              {/* score badge */}
              <span className={cn("text-xs font-bold mb-1", scoreColor(ps.score))}>
                {ps.score}
              </span>
              {/* summary */}
              <p className="text-[10px] text-zinc-400 text-center leading-tight px-1">
                {ps.summary}
              </p>
              {i < phaseSummaries.length - 1 && (
                <div className="absolute top-5 right-0 w-full h-px bg-zinc-700 -z-10" />
              )}
            </div>
          )
        })}
      </div>

      {footerNote && (
        <div className="mt-4 flex items-center gap-2 text-xs text-zinc-500">
          <span className="w-2 h-2 rounded-full bg-indigo-500 shrink-0" />
          {footerNote}
        </div>
      )}
    </div>
  )
}
