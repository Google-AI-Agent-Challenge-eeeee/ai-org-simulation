"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  fetchRequirements,
  acceptRequirements,
  reviseRequirements,
} from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"
import { REQUIREMENTS_BACKEND_LOGS } from "@/lib/constants"
import type { RequirementsSummary } from "@/lib/types"

export function useRequirementsReview(sessionId: string) {
  const router = useRouter()
  const { pmPersona, setRequirementsAccepted, appendBackendLog, clearBackendLogs } =
    useSessionStore()

  const [requirements, setRequirements] = useState<RequirementsSummary | null>(null)
  const [feedback, setFeedback]         = useState("")
  const [loading, setLoading]           = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError]               = useState<string | null>(null)

  useEffect(() => {
    clearBackendLogs()
    let logIdx = 0
    const logTimer = setInterval(() => {
      if (logIdx < REQUIREMENTS_BACKEND_LOGS.length) {
        appendBackendLog(REQUIREMENTS_BACKEND_LOGS[logIdx])
        logIdx++
      } else {
        clearInterval(logTimer)
      }
    }, 700)

    fetchRequirements(sessionId)
      .then((data) => {
        setRequirements(data)
        setLoading(false)
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "분석 실패")
        setLoading(false)
      })

    return () => clearInterval(logTimer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  async function handleAccept() {
    if (!requirements) return
    setActionLoading(true)
    try {
      await acceptRequirements(sessionId, feedback || undefined)
      setRequirementsAccepted(true)
      router.push(`/session/${sessionId}/teams`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "수락 실패")
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRevise() {
    setActionLoading(true)
    setLoading(true)
    clearBackendLogs()
    appendBackendLog("재검토 요청 접수됨 — 재분석 중…")
    try {
      const updated = await reviseRequirements(sessionId, feedback || "재검토 요청")
      setRequirements(updated)
      setFeedback("")
      REQUIREMENTS_BACKEND_LOGS.forEach((log, i) => {
        setTimeout(() => appendBackendLog(log), 600 * (i + 1))
      })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "재검토 실패")
    } finally {
      setActionLoading(false)
      setLoading(false)
    }
  }

  return {
    requirements,
    feedback, setFeedback,
    loading,
    actionLoading,
    error,
    pmPersona,
    handleAccept,
    handleRevise,
  }
}
