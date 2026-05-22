"use client"

import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import type { SessionStage } from "@/lib/types"

interface SessionHeaderProps {
  stage: SessionStage
}

export function SessionHeader({ stage }: SessionHeaderProps) {
  const router = useRouter()
  const isLive = stage === "meeting" || stage === "analyzing" || stage === "team_ready"

  return (
    <header className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800">
      <button
        type="button"
        onClick={() => router.push("/")}
        className="text-zinc-400 hover:text-zinc-200 transition-colors"
        aria-label="뒤로가기"
      >
        <ArrowLeft className="w-5 h-5" />
      </button>
      <div className="flex items-center gap-2">
        {isLive && (
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        )}
        <h1 className="text-sm font-semibold text-zinc-100">
          킥오프 회의 진행 중...
        </h1>
      </div>
    </header>
  )
}
