"use client"

import { useEffect, useState } from "react"
import { fetchReport } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"
import type { Report } from "@/lib/types"

export function useReport(sessionId: string) {
  const { pmPersona } = useSessionStore()
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    setLoading(true)
    fetchReport(sessionId, pmPersona)
      .then(setReport)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Unknown error"),
      )
      .finally(() => setLoading(false))
  }, [sessionId, pmPersona])

  return { report, loading, error }
}
