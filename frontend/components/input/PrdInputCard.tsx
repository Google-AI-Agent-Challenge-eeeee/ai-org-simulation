"use client"

import { FileText } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { TabGroup } from "./TabGroup"
import { FileDropzone } from "./FileDropzone"
import { Textarea } from "@/components/ui/textarea"

interface PrdInputCardProps {
  value: string
  onChange: (v: string) => void
  inputMode: "text" | "file"
  onModeChange: (mode: "text" | "file") => void
  onFileSelect: (file: File) => void
}

const TABS = [
  { id: "text", label: "직접 입력" },
  { id: "file", label: "파일 업로드" },
]

export function PrdInputCard({
  value,
  onChange,
  inputMode,
  onModeChange,
  onFileSelect,
}: PrdInputCardProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={FileText} title="PRD 입력" className="mb-3" />
      <TabGroup
        tabs={TABS}
        activeTab={inputMode}
        onChange={(id) => onModeChange(id as "text" | "file")}
      />
      {inputMode === "text" ? (
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="PRD 내용을 붙여넣으세요..."
          rows={8}
          className="resize-none bg-zinc-800 border-zinc-600 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500"
        />
      ) : (
        <FileDropzone onFileSelect={onFileSelect} />
      )}
    </div>
  )
}
