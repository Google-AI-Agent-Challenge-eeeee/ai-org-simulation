"use client"

import { use } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowLeft, ArrowRight, Users } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ProgressStepper } from "@/components/layout/ProgressStepper"
import { TeamRankCard } from "@/components/teams/TeamRankCard"
import { useTeamSelection } from "@/hooks/useTeamSelection"
import { fadeUp, staggerContainer } from "@/lib/motion"

interface Props {
  params: Promise<{ id: string }>
}

export default function TeamsPage({ params }: Props) {
  const { id: sessionId } = use(params)
  const router = useRouter()

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
    <div className="min-h-screen flex flex-col bg-[#0f0f13]">
      {/* 헤더 */}
      <header
        className="flex items-center justify-between px-8 py-4 border-b border-white/5 bg-[#0f0f13]/80 backdrop-blur-md"
      >
        <button
          type="button"
          onClick={() => router.back()}
          className="flex cursor-pointer items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          뒤로
        </button>
        <div />
      </header>

      {/* 스텝퍼 */}
      <div className="pt-6 pb-3 px-4">
        <ProgressStepper currentStep="teams" />
      </div>

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
          className="max-w-6xl mx-auto w-full px-4 pt-6 pb-12 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6"
        >
          <div className="flex flex-col gap-3">
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
          </div>

          <motion.aside
            variants={fadeUp}
            className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start"
          >
            <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-400" />
              팀 매칭 결정
            </h3>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-3">
                <p className="text-[11px] text-zinc-500 mb-1">총 조합 경우의 수</p>
                <p className="text-lg font-bold text-zinc-100">
                  {totalCombinations.toLocaleString()}
                </p>
              </div>
              <div className="rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-3">
                <p className="text-[11px] text-zinc-500 mb-1">분석 완료</p>
                <p className="text-lg font-bold text-zinc-100">상위 {teams.length}팀</p>
              </div>
            </div>

            {pmPersona && (
              <div className="flex items-center gap-3 rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-2">
                <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shrink-0">
                  <Users className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] text-zinc-500 mb-0.5">PM 페르소나</p>
                  <p className="text-sm font-medium text-zinc-100 truncate">{pmPersona.name}</p>
                </div>
              </div>
            )}

            <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 px-3 py-3">
              <p className="text-[11px] text-zinc-500 mb-1">선택된 팀 조합</p>
              {selectedTeam ? (
                <p className="text-sm font-semibold text-zinc-100">
                  #{selectedTeam.team_rank} {selectedTeam.team_name}
                  <span className="ml-1 text-indigo-400">({selectedTeam.team_fit_score})</span>
                </p>
              ) : (
                <p className="text-sm text-zinc-500">팀을 선택해주세요</p>
              )}
            </div>

            <Button
              onClick={handleConfirm}
              disabled={!selectedId || confirming}
              className="h-10 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
            >
              {confirming ? "시작 중..." : "이 팀으로 시뮬레이션 시작"}
              <ArrowRight className="w-4 h-4" />
            </Button>
          </motion.aside>
        </motion.div>
      )}
    </div>
  )
}
