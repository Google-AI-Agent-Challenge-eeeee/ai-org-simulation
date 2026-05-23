"use client"

import { LayoutList, Zap, Shield, Scale, Pencil } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { cn } from "@/lib/utils"
import { PM_STYLE_PRESETS } from "@/lib/constants"
import type { PmStylePreset } from "@/lib/constants"
import { Textarea } from "@/components/ui/textarea"

const PRESET_ICONS = {
  speed:   Zap,
  quality: Shield,
  balance: Scale,
  custom:  Pencil,
}

interface PmPriorityCardProps {
  selected: PmStylePreset
  onChange: (p: PmStylePreset) => void
  extra: string
  onExtraChange: (v: string) => void
}

export function PmPriorityCard({
  selected,
  onChange,
  extra,
  onExtraChange,
}: PmPriorityCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 flex flex-col gap-4">
      <SectionHeader icon={LayoutList} title="PM 운영 우선순위" className="mb-0" />
      <p className="text-xs text-zinc-500 -mt-2">요구사항 분석 시 가중치에 반영됩니다</p>

      <div className="grid grid-cols-4 gap-2">
        {PM_STYLE_PRESETS.map((p) => {
          const Icon = PRESET_ICONS[p.id]
          const isSelected = selected === p.id
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onChange(p.id)}
              className={cn(
                "flex flex-col items-center gap-1.5 rounded-xl border py-3 px-2 text-xs font-medium transition-all",
                isSelected
                  ? "bg-indigo-100 border-indigo-500 text-zinc-950 font-semibold"
                  : "bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200",
              )}
            >
              <Icon className="w-4 h-4" />
              {p.label}
            </button>
          )
        })}
      </div>

      {selected === "custom" && (
        <Textarea
          value={extra}
          onChange={(e) => onExtraChange(e.target.value)}
          placeholder="운영 우선순위 직접 입력..."
          rows={2}
          className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500"
        />
      )}
    </div>
  )
}
