"use client"

import { useRef, useState } from "react"
import { FileText, UploadCloud } from "lucide-react"
import { cn } from "@/lib/utils"

interface FileDropzoneProps {
  onFileSelect: (file: File) => void
  accept?: string
}

export function FileDropzone({
  onFileSelect,
  accept = "application/pdf,.pdf",
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [loadedFile, setLoadedFile] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  function processFile(file: File) {
    const acceptsPdf = accept.includes("pdf")
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
    if (acceptsPdf && !isPdf) return

    setLoadedFile(file.name)
    onFileSelect(file)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) processFile(file)
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) processFile(file)
    // 같은 파일 재선택 가능하도록 value 초기화
    e.target.value = ""
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex flex-col items-center justify-center gap-3 h-40 rounded-lg border-2 border-dashed cursor-pointer transition-colors",
        isDragging
          ? "border-indigo-400 bg-indigo-500/10"
          : loadedFile
            ? "border-emerald-500 bg-emerald-500/10"
            : "border-zinc-600 hover:border-indigo-500 bg-zinc-800/40",
      )}
    >
      {loadedFile ? (
        <div className="flex flex-col items-center gap-2 px-4 text-center">
          <div className="flex max-w-full items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2">
            <FileText className="h-4 w-4 shrink-0 text-emerald-400" />
            <p className="truncate text-sm font-medium text-emerald-300">{loadedFile}</p>
          </div>
          <p className="text-xs text-zinc-500">클릭하면 다른 파일로 교체</p>
        </div>
      ) : (
        <>
          <UploadCloud className={cn("w-8 h-8", isDragging ? "text-indigo-400" : "text-zinc-500")} />
          <p className="text-sm text-zinc-400">
            파일을 드래그하거나{" "}
            <span className="text-indigo-400 underline">클릭하여 선택</span>
          </p>
          <p className="text-xs text-zinc-600">PDF 파일만 지원</p>
        </>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={handleChange}
      />
    </div>
  )
}
