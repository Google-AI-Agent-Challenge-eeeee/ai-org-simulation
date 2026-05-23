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
    let active = true

    void Promise.resolve().then(async () => {
      setLoading(true)
      setError(null)

      try {
        const nextReport = await fetchReport(sessionId, pmPersona)
        if (active) setReport(nextReport)
      } catch (e: unknown) {
        if (active) {
          setError(e instanceof Error ? e.message : "Unknown error")
        }
      } finally {
        if (active) setLoading(false)
      }
    })

    return () => {
      active = false
    }
  }, [sessionId, pmPersona])

  return { report, loading, error }
}
