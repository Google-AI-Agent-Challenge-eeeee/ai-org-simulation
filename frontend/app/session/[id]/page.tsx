"use client"

import { use } from "react"
import { ArrowLeft, Pause, Play, X } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ProgressStepper } from "@/components/layout/ProgressStepper"
import { MeetingChat } from "@/components/session/MeetingChat"
import { SimulationSidebar } from "@/components/session/SimulationSidebar"
import { useSimulation } from "@/hooks/useSimulation"
import { useSessionStore } from "@/store/sessionStore"
import { PHASE_ORDER } from "@/lib/constants"
import { cn } from "@/lib/utils"

interface Props {
  params: Promise<{ id: string }>
}

function formatElapsed(seconds: number) {
  const m = String(Math.floor(seconds / 60)).padStart(2, "0")
  const s = String(seconds % 60).padStart(2, "0")
  return `${m}:${s}`
}

export default function SessionPage({ params }: Props) {
  const { id: sessionId } = use(params)
  const router = useRouter()

  useSimulation(sessionId)

  const { stage, messages, elapsed, isPaused, currentPhase, selectedTeam, togglePaused } =
    useSessionStore()

  const isDone    = stage === "done"
  const isLive    = stage === "meeting"
  const phaseIdx  = currentPhase ? PHASE_ORDER.indexOf(currentPhase) : 0
  const phaseProgress = isDone ? 100 : Math.round(((phaseIdx + 0.5) / PHASE_ORDER.length) * 100)

  return (
    <div className="flex flex-col h-screen bg-[#0f0f13]">
      {/* ── 헤더 ── */}
      <header
        className="flex items-center justify-between px-8 py-2.5 border-b border-white/5 bg-[#0f0f13]/80 backdrop-blur-md shrink-0"
      >
        <button
          type="button"
          onClick={() => router.back()}
          className="flex cursor-pointer items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
          aria-label="뒤로가기"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          뒤로
        </button>

        <div className="flex items-center gap-2 shrink-0">
          <span className="hidden sm:inline-flex h-7 items-center rounded-lg border border-zinc-700 bg-zinc-900 px-2.5 font-mono text-xs text-zinc-400">
            {formatElapsed(elapsed)}
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={togglePaused}
            disabled={!isLive}
            className={cn(
              "h-7 gap-1.5 border-zinc-700 px-2.5 text-xs font-semibold",
              isPaused
                ? "border-indigo-400/40 bg-indigo-500/15 text-indigo-400 hover:bg-indigo-500/25"
                : "bg-zinc-900 text-zinc-100 hover:bg-zinc-800",
            )}
          >
            {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
            {isPaused ? "재개" : "일시정지"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 border-red-500/50 bg-red-500/10 px-2.5 text-xs font-semibold text-red-400 hover:bg-red-500/20 hover:text-red-500"
          >
            <X className="w-3 h-3" />
            중단
          </Button>
        </div>
      </header>

      {/* ── Progress Stepper ── */}
      <div className="pt-6 pb-3 px-4 shrink-0">
        <ProgressStepper currentStep="simulation" />
      </div>

      {/* ── Main ── */}
      <div className="flex flex-1 min-h-0">
        {/* chat */}
        <div className="flex-1 min-w-0 px-4 pt-4 pb-8">
          <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/70">
            <div className="flex items-center justify-between border-b border-indigo-500/20 bg-indigo-100 px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-zinc-950">가상 킥오프 회의</p>
                <p className="text-xs text-indigo-950/65">AI 에이전트 협업 로그</p>
              </div>
              <span className={cn(
                "rounded-full px-2.5 py-1 text-[11px] font-semibold",
                isPaused
                  ? "bg-indigo-500/15 text-indigo-400"
                  : isLive
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "bg-zinc-800 text-zinc-500",
              )}>
                {isPaused ? "Paused" : isLive ? "Live" : "Ready"}
              </span>
            </div>
            <MeetingChat messages={messages} stage={stage} />
          </div>
        </div>

        {/* sidebar */}
        <div className="hidden w-72 shrink-0 px-4 pt-4 pb-8 lg:block">
          <SimulationSidebar
            selectedTeam={selectedTeam}
            teamFitScore={selectedTeam?.team_fit_score ?? 84}
            riskLevel="Moderate"
            phaseProgress={phaseProgress}
            canViewReport={isDone}
            onViewReport={() => router.push(`/report/${sessionId}`)}
          />
        </div>
      </div>
    </div>
  )
}
