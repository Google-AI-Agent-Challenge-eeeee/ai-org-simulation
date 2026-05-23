"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createSessionFromFile } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"
import type { PmStylePreset } from "@/lib/constants"

export function useInputForm() {
  const router = useRouter()
  const { setSessionId, setPmPersona, reset } = useSessionStore()

  const [prdFile, setPrdFile]     = useState<File | null>(null)

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
    prdFile !== null &&
    pmName.trim().length >= 1 &&
    pmPersona.trim().length >= 2

  function handleFileSelect(file: File) {
    setPrdFile(file)
  }

  async function handleSubmit() {
    if (!isValid || !prdFile) return
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
      const id = await createSessionFromFile({
        pmPersona: persona,
        pmPriority: priorityText,
      }, prdFile)
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
