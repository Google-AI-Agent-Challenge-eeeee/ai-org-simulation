import { cn } from "@/lib/utils"
import type { SessionStage } from "@/lib/types"

interface StatusBarProps {
  stage: SessionStage
  statusText: string
  elapsed: number
}

const STAGE_ORDER: SessionStage[] = [
  "idle",
  "analyzing",
  "team_ready",
  "meeting",
  "done",
]

function formatElapsed(seconds: number) {
  const m = String(Math.floor(seconds / 60)).padStart(2, "0")
  const s = String(seconds % 60).padStart(2, "0")
  return `00:${m}:${s}`
}

export function StatusBar({ stage, statusText, elapsed }: StatusBarProps) {
  const stageIndex = STAGE_ORDER.indexOf(stage)
  const progressPct = Math.round((stageIndex / (STAGE_ORDER.length - 1)) * 100)

  return (
    <div className="border-b border-zinc-800 bg-zinc-950">
      <div className="flex items-center justify-between px-4 py-2 text-xs text-zinc-400">
        <span className="font-bold text-zinc-300 uppercase tracking-wider">
          Phase 1
        </span>
        <span className={cn(statusText ? "text-zinc-300" : "text-zinc-600")}>
          {statusText || "대기 중..."}
        </span>
        <span className="font-mono">{formatElapsed(elapsed)}</span>
      </div>
      <div className="h-0.5 bg-zinc-800">
        <div
          className="h-full bg-indigo-500 transition-all duration-700"
          style={{ width: `${progressPct}%` }}
        />
      </div>
    </div>
  )
}
