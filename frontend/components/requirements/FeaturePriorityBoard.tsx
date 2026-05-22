import { cn } from "@/lib/utils"
import type { Feature } from "@/lib/types"

interface FeaturePriorityBoardProps {
  features: Feature[]
}

const PRIORITY_CONFIG = {
  P0: { label: "P0 (Critical)", dot: "bg-red-500",   border: "border-red-500/30",   text: "text-red-400"   },
  P1: { label: "P1 (High)",     dot: "bg-amber-500", border: "border-amber-500/30", text: "text-amber-400" },
  P2: { label: "P2 (Medium)",   dot: "bg-zinc-500",  border: "border-zinc-500/30",  text: "text-zinc-400"  },
}

function FeatureCard({ feature }: { feature: Feature }) {
  return (
    <div className="rounded-lg bg-zinc-800/50 border border-zinc-700 px-3 py-2 text-sm text-zinc-200">
      {feature.feature_name}
    </div>
  )
}

export function FeaturePriorityBoard({ features }: FeaturePriorityBoardProps) {
  const byPriority = {
    P0: features.filter((f) => f.priority === "P0"),
    P1: features.filter((f) => f.priority === "P1"),
    P2: features.filter((f) => f.priority === "P2"),
  }

  return (
    <div className="grid grid-cols-3 gap-3">
      {(["P0", "P1", "P2"] as const).map((priority) => {
        const cfg = PRIORITY_CONFIG[priority]
        return (
          <div
            key={priority}
            className={cn("rounded-xl border bg-zinc-900/60 p-3 flex flex-col gap-2", cfg.border)}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className={cn("w-2 h-2 rounded-full", cfg.dot)} />
              <span className={cn("text-xs font-semibold", cfg.text)}>
                {cfg.label}
              </span>
              <span className="ml-auto text-xs text-zinc-500">
                {byPriority[priority].length}
              </span>
            </div>
            {byPriority[priority].map((f) => (
              <FeatureCard key={f.feature_id} feature={f} />
            ))}
          </div>
        )
      })}
    </div>
  )
}
