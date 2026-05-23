"use client"

import { Download, FileText } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { FileDropzone } from "./FileDropzone"

interface PrdInputCardProps {
  onFileSelect: (file: File) => void
}

export function PrdInputCard({ onFileSelect }: PrdInputCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <SectionHeader icon={FileText} title="PRD 입력" className="mb-0" />
        <a
          href="/samples/notification-center-prd.pdf"
          download="PRD_001_notification_center_taxonomy_2page.pdf"
          className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 text-xs font-medium text-zinc-200 transition-colors hover:border-indigo-400 hover:text-indigo-300"
        >
          <Download className="h-3.5 w-3.5" />
          테스트용 PRD 파일
        </a>
      </div>
      <FileDropzone onFileSelect={onFileSelect} accept="application/pdf,.pdf" />
    </div>
  )
}
