"use client"

import { useState } from "react"
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"

interface RiskFlagsPanelProps {
  flags: string[]
}

export function RiskFlagsPanel({ flags }: RiskFlagsPanelProps) {
  const [open, setOpen] = useState(true)

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 text-left"
      >
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span className="text-sm font-semibold text-amber-300 flex-1">리스크 플래그 감지</span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-zinc-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        )}
      </button>

      {open && (
        <div className="mt-3 flex flex-wrap gap-2">
          {flags.map((flag, i) => (
            <span
              key={i}
              className={cn(
                "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border",
                "bg-amber-500/10 border-amber-500/30 text-amber-300",
              )}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              {flag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
