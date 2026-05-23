"use client"

import { User } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { Textarea } from "@/components/ui/textarea"

interface PmPersonaCardProps {
  name: string
  onNameChange: (v: string) => void
  persona: string
  onPersonaChange: (v: string) => void
  constraints: string
  onConstraintsChange: (v: string) => void
}

export function PmPersonaCard({
  name,
  onNameChange,
  persona,
  onPersonaChange,
  constraints,
  onConstraintsChange,
}: PmPersonaCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5 flex flex-col gap-4">
      <SectionHeader icon={User} title="PM 페르소나" className="mb-0" />

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

      {/* 성격 및 어조 */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-zinc-400 font-medium">
          성격 및 어조 <span className="text-[10px] text-zinc-600">(Personality &amp; Tone)</span>
        </label>
        <Textarea
          value={persona}
          onChange={(e) => onPersonaChange(e.target.value)}
          placeholder="단호하고 결단력 있음. 회의를 빠르게 진행하며 데이터 기반의 결정을 선호함."
          rows={3}
          className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500"
        />
      </div>

      {/* 필수 요구사항 */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-zinc-400 font-medium">
          필수 요구사항 <span className="text-[10px] text-zinc-600">(Required Constraints)</span>
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
