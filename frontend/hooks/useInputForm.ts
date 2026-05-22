"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createSession } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"
import type { PmStylePreset } from "@/lib/constants"

type InputMode = "text" | "file"

export function useInputForm() {
  const router = useRouter()
  const { setSessionId, setPmPersona, reset } = useSessionStore()

  const [prd, setPrd]             = useState("")
  const [inputMode, setInputMode] = useState<InputMode>("text")

  // PM Persona
  const [pmName, setPmName]             = useState("")
  const [pmPreset, setPmPreset]         = useState<PmStylePreset>("speed")
  const [pmPersona, setPmPersonaText]   = useState("")
  const [pmConstraints, setPmConstraints] = useState("")

  // PM Priority (separate card)
  const [pmPriority, setPmPriority]     = useState<PmStylePreset>("quality")
  const [pmPriorityExtra, setPmPriorityExtra] = useState("")

  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const isValid =
    prd.trim().length >= 20 &&
    pmName.trim().length >= 1 &&
    pmPersona.trim().length >= 10

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

    const persona = {
      name: pmName.trim(),
      preset: pmPreset,
      persona: pmPersona.trim(),
      constraints: pmConstraints.trim() || undefined,
    }

    const priorityText =
      pmPriority === "custom"
        ? pmPriorityExtra
        : `${pmPriority}${pmPriorityExtra ? ` / ${pmPriorityExtra}` : ""}`

    try {
      const id = await createSession({
        prd: prd.trim(),
        pmPersona: persona,
        pmPriority: priorityText,
      })
      setSessionId(id)
      setPmPersona(persona)
      router.push(`/session/${id}/requirements`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "시뮬레이션 시작 실패")
    } finally {
      setLoading(false)
    }
  }

  return {
    prd, setPrd,
    inputMode, setInputMode,
    pmName, setPmName,
    pmPreset, setPmPreset,
    pmPersona, setPmPersonaText,
    pmConstraints, setPmConstraints,
    pmPriority, setPmPriority,
    pmPriorityExtra, setPmPriorityExtra,
    loading, error, isValid,
    handleFileSelect,
    handleSubmit,
  }
}
