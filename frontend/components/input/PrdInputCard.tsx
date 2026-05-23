"use client"

import { FileText } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { FileDropzone } from "./FileDropzone"

interface PrdInputCardProps {
  onFileSelect: (file: File) => void
}

export function PrdInputCard({ onFileSelect }: PrdInputCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={FileText} title="PRD 입력" className="mb-3" />
      <FileDropzone onFileSelect={onFileSelect} accept="application/pdf,.pdf" />
    </div>
  )
}
