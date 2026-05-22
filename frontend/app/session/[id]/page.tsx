"use client"

import { use } from "react"
import { motion } from "framer-motion"
import { ArrowLeft, Pause, X, Info, ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { PhaseStepper } from "@/components/session/PhaseStepper"
import { MeetingChat } from "@/components/session/MeetingChat"
import { SimulationSidebar } from "@/components/session/SimulationSidebar"
import { BackendStatusStrip } from "@/components/layout/BackendStatusStrip"
import { useSimulation } from "@/hooks/useSimulation"
import { useSessionStore } from "@/store/sessionStore"
import { PHASE_META, PHASE_ORDER } from "@/lib/constants"
import { fadeDown } from "@/lib/motion"
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

  const { stage, messages, elapsed, currentPhase, backendLogs, selectedTeam } =
    useSessionStore()

  const isDone    = stage === "done"
  const isLive    = stage === "meeting"
  const phaseIdx  = currentPhase ? PHASE_ORDER.indexOf(currentPhase) : 0
  const phaseMeta = currentPhase ? PHASE_META[currentPhase] : PHASE_META.kickoff
  const phaseProgress = isDone ? 100 : Math.round(((phaseIdx + 0.5) / PHASE_ORDER.length) * 100)

  const pageTitle = isLive || isDone
    ? phaseMeta.label + (isDone ? " 완료" : " 진행 중…")
    : "시뮬레이션 준비 중…"

  return (
    <div className="flex flex-col h-screen bg-[#0f0f13]">
      {/* ── 헤더 ── */}
      <motion.header
        initial="hidden" animate="show" variants={fadeDown}
        className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800 shrink-0"
      >
        <button
          type="button"
          onClick={() => router.back()}
          className="text-zinc-400 hover:text-zinc-200 transition-colors"
          aria-label="뒤로가기"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 flex-1 min-w-0">
          {isLive && (
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          )}
          <h1 className="text-sm font-semibold text-zinc-100 truncate">
            {pageTitle}
          </h1>
          <span className="font-mono text-xs text-zinc-500 shrink-0">
            {formatElapsed(elapsed)}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5 border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-xs h-7"
          >
            <Pause className="w-3 h-3" />
            일시정지
          </Button>
          <Button
            size="sm"
            className="gap-1.5 bg-red-600/80 hover:bg-red-600 text-white text-xs h-7 border-0"
          >
            <X className="w-3 h-3" />
            시뮬레이션 중단
          </Button>
        </div>
      </motion.header>

      {/* ── Phase Stepper ── */}
      <div className="border-b border-zinc-800 shrink-0">
        <PhaseStepper currentPhase={currentPhase} isDone={isDone} />
        {/* sub-banner */}
        {currentPhase && (
          <div className="pb-2 flex justify-center">
            <span className="text-xs bg-zinc-800 border border-zinc-700 text-zinc-300 px-3 py-1 rounded-full">
              Phase {phaseIdx + 1}/5 · {phaseMeta.label} · {phaseMeta.subtitle}
            </span>
          </div>
        )}
      </div>

      {/* ── Main ── */}
      <div className="flex flex-1 min-h-0">
        {/* chat */}
        <div className="flex-1 min-w-0 flex flex-col">
          <MeetingChat messages={messages} stage={stage} />

          {/* footer */}
          <footer className="border-t border-zinc-800 bg-zinc-950 px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <Info className="w-3.5 h-3.5 shrink-0" />
              <span>5단계 시뮬레이션 완료 시 리포트 자동 생성</span>
            </div>
            <Button
              size="sm"
              disabled={!isDone}
              onClick={() => router.push(`/report/${sessionId}`)}
              className={cn(
                "gap-1.5 transition-all",
                isDone ? "bg-indigo-600 hover:bg-indigo-500 text-white" : "opacity-40",
              )}
            >
              리포트 보기
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </footer>
        </div>

        {/* sidebar */}
        <SimulationSidebar
          selectedTeam={selectedTeam}
          teamFitScore={selectedTeam?.team_fit_score ?? 84}
          riskLevel="Moderate"
          phaseProgress={phaseProgress}
        />
      </div>

      {/* ── Backend Log Strip ── */}
      <BackendStatusStrip logs={backendLogs} isActive={isLive} />
    </div>
  )
}
