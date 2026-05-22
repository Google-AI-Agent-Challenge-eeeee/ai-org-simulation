import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { PHASE_ORDER, PHASE_META } from "@/lib/constants"
import type { SimulationPhase } from "@/lib/types"

interface PhaseStepperProps {
  currentPhase: SimulationPhase | null
  isDone?: boolean
}

export function PhaseStepper({ currentPhase, isDone }: PhaseStepperProps) {
  const currentIdx = currentPhase ? PHASE_ORDER.indexOf(currentPhase) : -1

  return (
    <div className="flex items-start justify-center gap-0 py-3 px-4 overflow-x-auto">
      {PHASE_ORDER.map((phase, idx) => {
        const meta    = PHASE_META[phase]
        const isDone_ = isDone || idx < currentIdx
        const isActive = idx === currentIdx
        const isPending = idx > currentIdx

        return (
          <div key={phase} className="flex items-start">
            <div className="flex flex-col items-center gap-1.5 min-w-[72px]">
              <div
                className={cn(
                  "w-9 h-9 rounded-full border-2 flex items-center justify-center text-base transition-all",
                  isDone_   && "bg-indigo-600 border-indigo-600",
                  isActive  && "bg-indigo-600 border-indigo-400 ring-4 ring-indigo-500/20",
                  isPending && "bg-zinc-800 border-zinc-700",
                )}
              >
                {isDone_ ? (
                  <Check className="w-4 h-4 text-white" />
                ) : (
                  <span
                    className={cn(
                      "text-base leading-none",
                      isPending && "grayscale opacity-50",
                    )}
                  >
                    {meta.icon}
                  </span>
                )}
              </div>
              <span
                className={cn(
                  "text-[10px] font-medium text-center leading-tight",
                  isActive  ? "text-indigo-300" : "text-zinc-500",
                )}
              >
                {meta.label}
              </span>
            </div>

            {idx < PHASE_ORDER.length - 1 && (
              <div
                className={cn(
                  "h-px w-8 mt-4 mx-0.5 shrink-0",
                  idx < currentIdx ? "bg-indigo-600" : "bg-zinc-700",
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
