"use client"

import { Cpu, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PrdInputCard } from "@/components/input/PrdInputCard"
import { PmStyleCard } from "@/components/input/PmStyleCard"
import { useInputForm } from "@/hooks/useInputForm"

export default function InputPage() {
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
      <header className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-bold text-zinc-100">AI Org Simulation</span>
        </div>
      </header>

      {/* 본문 */}
      <main className="flex-1 flex flex-col items-center py-10 px-4">
        <div className="w-full max-w-2xl flex flex-col gap-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-zinc-100 mb-2">시뮬레이션 입력</h1>
            <p className="text-sm text-zinc-400">
              조직 구조 최적화를 위한 요구사항과 PRD를 입력하세요.
            </p>
          </div>

          <PrdInputCard
            value={prd}
            onChange={setPrd}
            inputMode={inputMode}
            onModeChange={setInputMode}
            onFileSelect={handleFileSelect}
          />

          <PmStyleCard
            preset={pmPreset}
            onPresetChange={setPmPreset}
            extra={pmExtra}
            onExtraChange={setPmExtra}
          />

          {error && (
            <p className="text-sm text-red-400 text-center">{error}</p>
          )}

          <Button
            size="lg"
            disabled={!isValid || loading}
            onClick={handleSubmit}
            className="w-full gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-4 text-base"
          >
            {loading ? "시작 중..." : "시뮬레이션 시작"}
            {!loading && <ArrowRight className="w-4 h-4" />}
          </Button>
        </div>
      </main>
    </div>
  )
}
