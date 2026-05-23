"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PrdInputCard } from "@/components/input/PrdInputCard"
import { PmPersonaCard } from "@/components/input/PmPersonaCard"
import { PmPriorityCard } from "@/components/input/PmPriorityCard"
import { useInputForm } from "@/hooks/useInputForm"
import { fadeUp, staggerContainer } from "@/lib/motion"

export default function SimulatePage() {
  const {
    pmName, setPmName,
    pmPersona, setPmPersonaText,
    pmConstraints, setPmConstraints,
    pmPriority, setPmPriority,
    pmPriorityExtra, setPmPriorityExtra,
    loading, error, isValid,
    handleFileSelect,
    handleSubmit,
  } = useInputForm()

  return (
    <div className="min-h-screen flex flex-col bg-[#0f0f13]">
      {/* 헤더 */}
      <header
        className="flex items-center justify-between px-8 py-4 border-b border-white/5 bg-[#0f0f13]/80 backdrop-blur-md"
      >
        <Link href="/" className="cursor-pointer text-xs text-zinc-400 hover:text-zinc-200 transition-colors">
          HOME
        </Link>
        <div />
      </header>

      {/* 본문 */}
      <main className="flex-1 flex flex-col items-center py-10 px-4 pb-20">
        <motion.div
          initial="hidden" animate="show"
          variants={staggerContainer(0.1, 0.15)}
          className="w-full max-w-2xl flex flex-col gap-6"
        >
          <motion.div variants={fadeUp} className="text-center">
            <h1 className="text-3xl font-bold text-zinc-100 mb-2">PRD 입력</h1>
            <p className="text-sm text-zinc-400">
              PRD와 PM 페르소나를 입력하면 AI가 추천한 팀 조합을 바탕으로 가상 킥오프 회의를 시뮬레이션합니다.
            </p>
          </motion.div>

          <motion.div variants={fadeUp}>
            <PrdInputCard
              onFileSelect={handleFileSelect}
            />
          </motion.div>

          <motion.div variants={fadeUp}>
            <PmPersonaCard
              name={pmName}
              onNameChange={setPmName}
              persona={pmPersona}
              onPersonaChange={setPmPersonaText}
              constraints={pmConstraints}
              onConstraintsChange={setPmConstraints}
            />
          </motion.div>

          <motion.div variants={fadeUp}>
            <PmPriorityCard
              selected={pmPriority}
              onChange={setPmPriority}
              extra={pmPriorityExtra}
              onExtraChange={setPmPriorityExtra}
            />
          </motion.div>

          {error && (
            <motion.p
              initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }}
              className="text-sm text-red-400 text-center"
            >
              {error}
            </motion.p>
          )}

          <motion.div variants={fadeUp}>
            <Button
              size="lg"
              disabled={!isValid || loading}
              onClick={handleSubmit}
              className="w-full h-12 gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-semibold text-base"
            >
              {loading ? "분석 시작 중..." : "요구사항 분석 시작"}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </Button>
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}
