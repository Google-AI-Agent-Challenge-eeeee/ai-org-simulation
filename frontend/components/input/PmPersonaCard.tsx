"use client"

import { User, Info } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { PresetChip } from "@/components/ui/preset-chip"
import { Textarea } from "@/components/ui/textarea"
import { PM_STYLE_PRESETS } from "@/lib/constants"
import type { PmStylePreset } from "@/lib/constants"

interface PmPersonaCardProps {
  name: string
  onNameChange: (v: string) => void
  preset: PmStylePreset
  onPresetChange: (p: PmStylePreset) => void
  persona: string
  onPersonaChange: (v: string) => void
  constraints: string
  onConstraintsChange: (v: string) => void
}

export function PmPersonaCard({
  name,
  onNameChange,
  preset,
  onPresetChange,
  persona,
  onPersonaChange,
  constraints,
  onConstraintsChange,
}: PmPersonaCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 flex flex-col gap-4">
      <SectionHeader icon={User} title="PM 페르소나" className="mb-0" />

      {/* info banner */}
      <div className="flex items-start gap-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-3 py-2">
        <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
        <p className="text-xs text-indigo-300 leading-relaxed">
          PM은 직원 DB에 없습니다. 시뮬레이션을 주도할 PM의 특성을 정의해주세요.
        </p>
      </div>

      {/* PM 이름 */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-zinc-400 font-medium">PM 이름</label>
        <input
          type="text"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Alex (기본)"
          className="w-full rounded-lg bg-zinc-800 border border-zinc-600 text-zinc-100 text-sm px-3 py-2 placeholder:text-zinc-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
      </div>

      {/* 스타일 프리셋 */}
      <div className="flex flex-col gap-2">
        <label className="text-xs text-zinc-400 font-medium">스타일 프리셋</label>
        <div className="flex flex-wrap gap-2">
          {PM_STYLE_PRESETS.map((p) => (
            <PresetChip
              key={p.id}
              label={p.label}
              selected={preset === p.id}
              onClick={() => onPresetChange(p.id)}
            />
          ))}
        </div>
      </div>

      {/* 성격 및 이즈 */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-zinc-400 font-medium">
          성격 및 이즈 <span className="text-[10px] text-zinc-600">(Personality &amp; Tone)</span>
        </label>
        <Textarea
          value={persona}
          onChange={(e) => onPersonaChange(e.target.value)}
          placeholder="단호하고 결단력 있음. 회의를 빠르게 진행하며 데이터 기반의 결정을 선호함."
          rows={3}
          className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500"
        />
      </div>

      {/* 제약 사항 */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-zinc-400 font-medium">
          제약 사항 <span className="text-[10px] text-zinc-600">(Constraints)</span>{" "}
          <span className="text-zinc-600">선택</span>
        </label>
        <Textarea
          value={constraints}
          onChange={(e) => onConstraintsChange(e.target.value)}
          placeholder="예: 예산 한도 내에서만 결정, 특정 기술 스택 필수 등..."
          rows={2}
          className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500"
        />
      </div>
    </div>
  )
}
