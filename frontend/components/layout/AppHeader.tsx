"use client"

import { Cpu, Copy, Download } from "lucide-react"
import { Button } from "@/components/ui/button"

interface AppHeaderProps {
  /** 리포트 페이지에서 제목/날짜 표시 */
  reportTitle?: string
  reportCreatedAt?: string
  onCopyLink?: () => void
  onDownloadJson?: () => void
}

export function AppHeader({
  reportTitle,
  reportCreatedAt,
  onCopyLink,
  onDownloadJson,
}: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
      <div className="flex items-center gap-2">
        <Cpu className="w-5 h-5 text-indigo-400" />
        <span className="text-sm font-bold text-zinc-100">AI Org Simulation</span>
      </div>

      {reportTitle && (
        <div className="hidden sm:flex flex-col items-center">
          <span className="text-sm font-semibold text-zinc-200">{reportTitle}</span>
          {reportCreatedAt && (
            <span className="text-xs text-zinc-500">생성 일시: {reportCreatedAt}</span>
          )}
        </div>
      )}

      {(onCopyLink || onDownloadJson) && (
        <div className="flex items-center gap-2">
          {onCopyLink && (
            <Button variant="outline" size="sm" onClick={onCopyLink} className="gap-1.5 border-zinc-700 text-zinc-300 hover:text-white">
              <Copy className="w-3.5 h-3.5" />
              링크 복사
            </Button>
          )}
          {onDownloadJson && (
            <Button size="sm" onClick={onDownloadJson} className="gap-1.5">
              <Download className="w-3.5 h-3.5" />
              JSON 다운로드
            </Button>
          )}
        </div>
      )}

      {!reportTitle && !onCopyLink && (
        <div className="w-24" /> /* spacer */
      )}
    </header>
  )
}
