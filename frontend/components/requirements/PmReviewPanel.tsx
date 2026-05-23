"use client"

import { Check, RotateCcw, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import type { PmPersona } from "@/lib/types"
import type { PmStylePreset } from "@/lib/constants"
import { PM_STYLE_PRESETS } from "@/lib/constants"

interface PmReviewPanelProps {
  confidence: number
  pmPersona: PmPersona | null
  feedback: string
  onFeedbackChange: (v: string) => void
  onAccept: () => void
  onRevise: () => void
  isLoading: boolean
}

const PRESET_LABELS: Record<PmStylePreset, string> = Object.fromEntries(
  PM_STYLE_PRESETS.map((p) => [p.id, p.label]),
) as Record<PmStylePreset, string>

export function PmReviewPanel({
  confidence,
  pmPersona,
  feedback,
  onFeedbackChange,
  onAccept,
  onRevise,
  isLoading,
}: PmReviewPanelProps) {
  const confidenceLabel =
    confidence >= 85 ? "높음" : confidence >= 60 ? "중간" : "낮음"
  const confidenceColor =
    confidence >= 85 ? "text-emerald-400" : confidence >= 60 ? "text-amber-400" : "text-red-400"

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 flex flex-col gap-4 sticky top-4">
      <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
        <span className="w-4 h-4 text-indigo-400">🎯</span>
        PM 검토 및 결정
      </h3>

      {/* 신뢰도 */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-zinc-400">요구사항 분석 신뢰도</span>
          <span className={cn("text-xs font-bold", confidenceColor)}>
            {confidence}% ({confidenceLabel})
          </span>
        </div>
        <div className="h-1.5 rounded-full bg-zinc-700">
          <div
            className="h-full rounded-full bg-indigo-500 transition-all duration-700"
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      {/* PM 페르소나 요약 */}
      {pmPersona && (
        <div className="flex items-center gap-3 rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shrink-0">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] text-zinc-500 mb-0.5">배정된 PM 페르소나</p>
            <p className="text-sm font-medium text-zinc-100">{pmPersona.name}</p>
          </div>
          <span className="text-xs bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 px-2 py-0.5 rounded-full shrink-0">
            {PRESET_LABELS[pmPersona.preset]}
          </span>
        </div>
      )}

      {/* 피드백 */}
      <div>
        <label className="text-xs text-zinc-400 mb-1.5 block">수정 요청 사항 (선택)</label>
        <Textarea
          value={feedback}
          onChange={(e) => onFeedbackChange(e.target.value)}
          placeholder="재검토 시 반영할 피드백을 입력하세요..."
          rows={3}
          className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 text-sm"
        />
      </div>

      {/* CTA */}
      <div className="flex flex-col gap-2">
        <Button
          variant="outline"
          onClick={onRevise}
          disabled={isLoading}
          className="w-full h-10 border-zinc-600 text-zinc-300 hover:bg-zinc-800 gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          재검토 요청
        </Button>
        <Button
          onClick={onAccept}
          disabled={isLoading}
          className="w-full h-10 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold gap-2"
        >
          <Check className="w-4 h-4" />
          팀 매칭 시작
        </Button>
      </div>
    </div>
  )
}
