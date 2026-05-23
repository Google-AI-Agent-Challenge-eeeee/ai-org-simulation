"use client"

import { cn } from "@/lib/utils"

interface BackendStatusStripProps {
  logs: string[]
  isActive?: boolean
  className?: string
}

export function BackendStatusStrip({
  logs,
  isActive = false,
  className,
}: BackendStatusStripProps) {
  const display = logs.length === 0
    ? ["대기 중 — PRD와 PM 페르소나를 입력하세요"]
    : logs.slice(-4)

  return (
    <div
      className={cn(
        "border-t border-zinc-200 bg-white/90 px-4 py-2 flex items-center gap-3 min-h-[36px] backdrop-blur-md",
        className,
      )}
    >
      <div className="flex-1 flex items-center gap-2 overflow-hidden">
        {display.map((line, i) => {
          const isCurrent = i === display.length - 1
          return (
            <span key={`${line}-${i}`} className="flex items-center gap-2 shrink-0">
              {i > 0 && <span className="text-zinc-300 select-none">·</span>}
              <span
                className={cn(
                  "font-mono text-[11px] truncate transition-colors",
                  isCurrent ? "text-zinc-600" : "text-zinc-400",
                )}
              >
                {line}
              </span>
            </span>
          )
        })}
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            isActive ? "bg-emerald-500 animate-pulse" : "bg-zinc-300",
          )}
        />
        <span className="font-mono text-[10px] text-zinc-400">
          {isActive ? "Active" : "Idle"}
        </span>
      </div>
    </div>
  )
}
