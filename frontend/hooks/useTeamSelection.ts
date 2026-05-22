"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { fetchTeamCandidates, selectTeam } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"
import { TEAMS_BACKEND_LOGS } from "@/lib/constants"
import type { TeamCandidate } from "@/lib/types"

export function useTeamSelection(sessionId: string) {
  const router = useRouter()
  const { pmPersona, setSelectedTeam, appendBackendLog, clearBackendLogs } = useSessionStore()

  const [teams, setTeams]             = useState<TeamCandidate[]>([])
  const [totalCombinations, setTotal] = useState(0)
  const [selectedId, setSelectedId]   = useState<string | null>(null)
  const [loading, setLoading]         = useState(true)
  const [confirming, setConfirming]   = useState(false)
  const [error, setError]             = useState<string | null>(null)

  useEffect(() => {
    clearBackendLogs()
    let logIdx = 0
    const logTimer = setInterval(() => {
      if (logIdx < TEAMS_BACKEND_LOGS.length) {
        appendBackendLog(TEAMS_BACKEND_LOGS[logIdx])
        logIdx++
      } else {
        clearInterval(logTimer)
      }
    }, 800)

    fetchTeamCandidates(sessionId)
      .then(({ totalCombinations: total, teams: data }) => {
        setTeams(data)
        setTotal(total)
        // pre-select rank 1
        if (data.length > 0) setSelectedId(data[0].team_id)
        setLoading(false)
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "팀 조회 실패")
        setLoading(false)
      })

    return () => clearInterval(logTimer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  function handleSelect(teamId: string) {
    setSelectedId(teamId)
  }

  async function handleConfirm() {
    if (!selectedId) return
    const team = teams.find((t) => t.team_id === selectedId)
    if (!team) return

    setConfirming(true)
    try {
      await selectTeam(sessionId, selectedId)
      setSelectedTeam(team)
      router.push(`/session/${sessionId}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "팀 선택 실패")
    } finally {
      setConfirming(false)
    }
  }

  const selectedTeam = teams.find((t) => t.team_id === selectedId) ?? null

  return {
    teams,
    totalCombinations,
    selectedId,
    selectedTeam,
    loading,
    confirming,
    error,
    pmPersona,
    handleSelect,
    handleConfirm,
  }
}
