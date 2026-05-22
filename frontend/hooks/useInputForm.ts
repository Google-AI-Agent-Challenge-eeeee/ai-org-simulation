"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createSession } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"
import type { PmStylePreset } from "@/lib/constants"

type InputMode = "text" | "file"

export function useInputForm() {
  const router = useRouter()
  const { setSessionId, reset } = useSessionStore()

  const [prd, setPrd] = useState("")
  const [inputMode, setInputMode] = useState<InputMode>("text")
  const [pmPreset, setPmPreset] = useState<PmStylePreset>("balance")
  const [pmExtra, setPmExtra] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isValid = prd.trim().length >= 20

  function handleFileSelect(file: File) {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      setPrd(text ?? "")
    }
    reader.readAsText(file, "utf-8")
  }

  async function handleSubmit() {
    if (!isValid) return
    setError(null)
    setLoading(true)
    reset()

    const pmStyle =
      pmPreset === "custom"
        ? pmExtra
        : `${pmPreset}${pmExtra ? ` / ${pmExtra}` : ""}`

    try {
      const id = await createSession({ prd: prd.trim(), pmStyle })
      setSessionId(id)
      router.push(`/session/${id}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "시뮬레이션 시작 실패")
    } finally {
      setLoading(false)
    }
  }

  return {
    prd, setPrd,
    inputMode, setInputMode,
    pmPreset, setPmPreset,
    pmExtra, setPmExtra,
    loading, error, isValid,
    handleFileSelect,
    handleSubmit,
  }
}
