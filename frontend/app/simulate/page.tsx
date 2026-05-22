"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Cpu, ArrowRight, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PrdInputCard } from "@/components/input/PrdInputCard"
import { PmStyleCard } from "@/components/input/PmStyleCard"
import { useInputForm } from "@/hooks/useInputForm"
import { fadeDown, fadeUp, staggerContainer } from "@/lib/motion"

export default function SimulatePage() {
  const {
    prd, setPrd,
    inputMode, setInputMode,
    pmPreset, setPmPreset,
    pmExtra, setPmExtra,
    loading, error, isValid,
    handleFileSelect,
    handleSubmit,
  } = useInputForm()

  return (
    <div className="min-h-screen flex flex-col">
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
      <main className="flex-1 flex flex-col items-center py-10 px-4">
        <motion.div
          initial="hidden" animate="show"
          variants={staggerContainer(0.1, 0.15)}
          className="w-full max-w-2xl flex flex-col gap-6"
        >
          <motion.div variants={fadeUp} className="text-center">
            <h1 className="text-3xl font-bold text-zinc-100 mb-2">시뮬레이션 입력</h1>
            <p className="text-sm text-zinc-400">
              조직 구조 최적화를 위한 요구사항과 PRD를 입력하세요.
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
            <PmStyleCard
              preset={pmPreset}
              onPresetChange={setPmPreset}
              extra={pmExtra}
              onExtraChange={setPmExtra}
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
              className="w-full gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-4 text-base"
            >
              {loading ? "시작 중..." : "시뮬레이션 시작"}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </Button>
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}
