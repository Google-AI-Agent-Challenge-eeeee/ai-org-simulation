"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Cpu, ArrowRight, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PrdInputCard } from "@/components/input/PrdInputCard"
import { PmPersonaCard } from "@/components/input/PmPersonaCard"
import { PmPriorityCard } from "@/components/input/PmPriorityCard"
import { BackendStatusStrip } from "@/components/layout/BackendStatusStrip"
import { useInputForm } from "@/hooks/useInputForm"
import { fadeDown, fadeUp, staggerContainer } from "@/lib/motion"

export default function SimulatePage() {
  const {
    prd, setPrd,
    inputMode, setInputMode,
    pmName, setPmName,
    pmPreset, setPmPreset,
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
      <motion.header
        initial="hidden" animate="show" variants={fadeDown}
        className="flex items-center justify-between px-5 py-4 border-b border-zinc-800"
      >
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-bold text-zinc-100">AI Org Simulation</span>
        </Link>
        <Link href="/" className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
          홈으로
        </Link>
      </motion.header>

      {/* 본문 */}
      <main className="flex-1 flex flex-col items-center py-10 px-4 pb-20">
        <motion.div
          initial="hidden" animate="show"
          variants={staggerContainer(0.1, 0.15)}
          className="w-full max-w-2xl flex flex-col gap-6"
        >
          <motion.div variants={fadeUp} className="text-center">
            <h1 className="text-3xl font-bold text-zinc-100 mb-2">시뮬레이션 입력</h1>
            <p className="text-sm text-zinc-400">
              PRD와 PM 페르소나를 입력하면 AI가 팀 조합과 가상 회의를 시뮬레이션합니다.
            </p>
          </motion.div>

          <motion.div variants={fadeUp}>
            <PrdInputCard
              value={prd}
              onChange={setPrd}
              inputMode={inputMode}
              onModeChange={setInputMode}
              onFileSelect={handleFileSelect}
              onFileLoaded={() => setInputMode("text")}
            />
          </motion.div>

          <motion.div variants={fadeUp}>
            <PmPersonaCard
              name={pmName}
              onNameChange={setPmName}
              preset={pmPreset}
              onPresetChange={setPmPreset}
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
              className="w-full gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-semibold py-4 text-base"
            >
              {loading ? "분석 시작 중..." : "요구사항 분석 시작"}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </Button>
          </motion.div>
        </motion.div>
      </main>

      {/* 하단 백엔드 로그 */}
      <div className="fixed bottom-0 left-0 right-0">
        <BackendStatusStrip logs={[]} isActive={loading} />
      </div>
    </div>
  )
}
