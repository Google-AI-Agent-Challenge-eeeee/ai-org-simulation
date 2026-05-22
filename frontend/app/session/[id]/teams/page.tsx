"use client"

import { use } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowLeft, ArrowRight, Users } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ProgressStepper } from "@/components/layout/ProgressStepper"
import { BackendStatusStrip } from "@/components/layout/BackendStatusStrip"
import { TeamRankCard } from "@/components/teams/TeamRankCard"
import { useTeamSelection } from "@/hooks/useTeamSelection"
import { useSessionStore } from "@/store/sessionStore"
import { fadeDown, fadeUp, staggerContainer } from "@/lib/motion"

interface Props {
  params: Promise<{ id: string }>
}

export default function TeamsPage({ params }: Props) {
  const { id: sessionId } = use(params)
  const router = useRouter()
  const { backendLogs } = useSessionStore()

  const {
    teams,
    totalCombinations,
    selectedId,
    selectedTeam,
    loading,
    confirming,
    error,
    pmPersona,
    handleSelect,
    handleConfirm,
  } = useTeamSelection(sessionId)

  return (
    <div className="min-h-screen flex flex-col bg-[#0f0f13] pb-24">
      {/* 헤더 */}
      <motion.header
        initial="hidden" animate="show" variants={fadeDown}
        className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 sticky top-0 z-20 bg-[#0f0f13]/95 backdrop-blur"
      >
        <button
          type="button"
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="text-center">
          <h1 className="text-sm font-semibold text-zinc-100">팀 조합 선택</h1>
          <p className="text-[11px] text-zinc-500">적합도 점수 기준 상위 10팀</p>
        </div>
        {/* mini stepper */}
        <div className="hidden md:flex items-center gap-2 text-xs text-zinc-500">
          {["목표", "조건", "팀 선택"].map((label, i) => (
            <span key={label} className="flex items-center gap-1.5">
              {i > 0 && <span className="text-zinc-700">—</span>}
              <span
                className={i === 2 ? "text-indigo-400 font-semibold" : ""}
              >
                {i + 1} {label}
              </span>
            </span>
          ))}
        </div>
      </motion.header>

      {/* 스텝퍼 */}
      <div className="border-b border-zinc-800 py-3 px-4 md:hidden">
        <ProgressStepper currentStep="teams" />
      </div>

      {/* 요약 strip */}
      {!loading && (
        <div className="border-b border-zinc-800 bg-zinc-900/40 px-5 py-3 flex items-center gap-6 flex-wrap text-sm">
          <div>
            <span className="text-zinc-500 text-xs">총 조합 경우의 수</span>
            <p className="font-bold text-zinc-100 text-lg">
              {totalCombinations.toLocaleString()}
            </p>
          </div>
          <div className="h-6 w-px bg-zinc-700" />
          <div>
            <span className="text-zinc-500 text-xs">분석 완료</span>
            <p className="font-semibold text-zinc-200">상위 {teams.length}팀</p>
          </div>
          {pmPersona && (
            <>
              <div className="h-6 w-px bg-zinc-700" />
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-400" />
                <span className="text-zinc-200 font-medium">PM: {pmPersona.name}</span>
              </div>
            </>
          )}
        </div>
      )}

      {/* 오류 */}
      {error && (
        <div className="mx-4 mt-4 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* 로딩 */}
      {loading && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <p className="text-sm text-zinc-400 animate-pulse">팀 조합 계산 중...</p>
        </div>
      )}

      {/* 팀 리스트 */}
      {!loading && (
        <motion.div
          initial="hidden" animate="show"
          variants={staggerContainer(0.05, 0.05)}
          className="max-w-4xl mx-auto w-full px-4 pt-5 flex flex-col gap-3"
        >
          <AnimatePresence>
            {teams.map((team) => (
              <motion.div key={team.team_id} variants={fadeUp}>
                <TeamRankCard
                  team={team}
                  isSelected={selectedId === team.team_id}
                  onSelect={handleSelect}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* 하단 sticky 선택 바 */}
      <div className="fixed bottom-0 left-0 right-0 z-30">
        {selectedTeam && (
          <div className="border-t border-zinc-800 bg-zinc-950/95 backdrop-blur px-4 py-3 flex items-center justify-between">
            <span className="text-sm text-zinc-300 font-medium">
              선택된 팀 조합:{" "}
              <span className="text-zinc-100 font-bold">
                #{selectedTeam.team_rank} {selectedTeam.team_name}
              </span>{" "}
              <span className="text-indigo-400">({selectedTeam.team_fit_score})</span>
            </span>
            <Button
              onClick={handleConfirm}
              disabled={!selectedId || confirming}
              className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
            >
              {confirming ? "시작 중..." : "이 팀으로 시뮬레이션 시작"}
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        )}
        <BackendStatusStrip logs={backendLogs} isActive={loading} />
      </div>
    </div>
  )
}
