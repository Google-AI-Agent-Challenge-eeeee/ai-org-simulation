"use client"

import { SlidersHorizontal } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { PresetChipGroup } from "./PresetChipGroup"
import { Textarea } from "@/components/ui/textarea"
import type { PmStylePreset } from "@/lib/constants"

interface PmStyleCardProps {
  preset: PmStylePreset
  onPresetChange: (p: PmStylePreset) => void
  extra: string
  onExtraChange: (v: string) => void
}

export function PmStyleCard({
  preset,
  onPresetChange,
  extra,
  onExtraChange,
}: PmStyleCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={SlidersHorizontal} title="PM 요구사항" className="mb-3" />
      <p className="text-xs text-zinc-500 mb-2">우선순위 설정</p>
      <PresetChipGroup selected={preset} onChange={onPresetChange} />
      <p className="text-xs text-zinc-500 mt-4 mb-2">추가 요구사항 (선택)</p>
      <Textarea
        value={extra}
        onChange={(e) => onExtraChange(e.target.value)}
        placeholder="추가적인 조직 제약사항이나 목표를 입력하세요..."
        rows={3}
        className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500"
      />
    </div>
  )
}
