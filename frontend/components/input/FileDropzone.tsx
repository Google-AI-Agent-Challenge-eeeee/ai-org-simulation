"use client"

import { useRef } from "react"
import { UploadCloud } from "lucide-react"

interface FileDropzoneProps {
  onFileSelect: (file: File) => void
  accept?: string
}

export function FileDropzone({
  onFileSelect,
  accept = ".md,.txt",
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) onFileSelect(file)
  }

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className="flex flex-col items-center justify-center gap-3 h-40 rounded-lg border-2 border-dashed border-zinc-600 hover:border-indigo-500 bg-zinc-800/40 cursor-pointer transition-colors"
    >
      <UploadCloud className="w-8 h-8 text-zinc-500" />
      <p className="text-sm text-zinc-400">
        파일을 드래그하거나{" "}
        <span className="text-indigo-400 underline">클릭하여 선택</span>
      </p>
      <p className="text-xs text-zinc-600">.md, .txt 지원</p>
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
