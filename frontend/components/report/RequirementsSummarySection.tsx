"use client"

import { useState } from "react"
import { FileText, ChevronDown, ChevronUp, CheckCircle } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import type { RequirementsAcceptedSummary } from "@/lib/types"

interface RequirementsSummarySectionProps {
  data: RequirementsAcceptedSummary
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("ko-KR", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  }) + " UTC"
}

export function RequirementsSummarySection({ data }: RequirementsSummarySectionProps) {
  const [open, setOpen] = useState(true)

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <div className="flex items-center justify-between">
        <SectionHeader icon={FileText} title="요구사항 분석 요약" className="mb-0" />
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {open && (
        <div className="mt-4 flex flex-col gap-3">
          <p className="text-xs text-zinc-500">
            Accepted:{" "}
            <span className="text-zinc-400">{formatDate(data.acceptedAt)}</span>
          </p>

          <div className="flex flex-col gap-2">
            {data.bullets.map((bullet, i) => (
              <div key={i} className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <p className="text-sm text-zinc-300 leading-relaxed">{bullet}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
