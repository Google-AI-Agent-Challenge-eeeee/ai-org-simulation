"use client"

import { Info, ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import type { SessionStage } from "@/lib/types"

interface SessionFooterProps {
  stage: SessionStage
  sessionId: string
}

export function SessionFooter({ stage, sessionId }: SessionFooterProps) {
  const router = useRouter()
  const isDone = stage === "done"

  return (
    <footer className="border-t border-zinc-800 bg-zinc-950 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <Info className="w-3.5 h-3.5 shrink-0" />
        <span>회의가 완료되면 리포트가 자동 생성됩니다</span>
      </div>
      <Button
        size="sm"
        disabled={!isDone}
        onClick={() => router.push(`/report/${sessionId}`)}
        className="gap-1.5"
      >
        리포트 보기
        <ArrowRight className="w-3.5 h-3.5" />
      </Button>
    </footer>
  )
}
