/**
 * API 레이어
 *
 * NEXT_PUBLIC_MOCK=true 환경변수 시 mock 시나리오 반환.
 * 컴포넌트/훅은 mock 여부를 알 필요 없음 — 이 파일에서만 분기.
 */

import { BACKEND_BASE_URL } from "./constants"
import type {
  Report,
  SimulationInput,
  RequirementsSummary,
  TeamCandidate,
} from "./types"
import { startMockSession, getMockReport } from "./mock/scenario"
import { MOCK_REQUIREMENTS } from "./mock/requirements"
import { MOCK_TEAMS } from "./mock/teams"

const isMock = process.env.NEXT_PUBLIC_MOCK === "true"

/* ─── Session ─────────────────────────── */

export async function createSession(input: SimulationInput): Promise<string> {
  if (isMock) return startMockSession()

  const res = await fetch(`${BACKEND_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error(`createSession failed: ${res.status}`)
  const { session_id } = (await res.json()) as { session_id: string }
  return session_id
}

/* ─── Requirements ────────────────────── */

export async function fetchRequirements(
  _sessionId: string,
): Promise<RequirementsSummary> {
  if (isMock) {
    await delay(1200)
    return MOCK_REQUIREMENTS
  }
  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${_sessionId}/requirements`,
  )
  if (!res.ok) throw new Error(`fetchRequirements failed: ${res.status}`)
  return res.json() as Promise<RequirementsSummary>
}

export async function acceptRequirements(
  sessionId: string,
  feedback?: string,
): Promise<void> {
  if (isMock) {
    await delay(600)
    return
  }
  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${sessionId}/requirements/accept`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback }),
    },
  )
  if (!res.ok) throw new Error(`acceptRequirements failed: ${res.status}`)
}

export async function reviseRequirements(
  sessionId: string,
  feedback: string,
): Promise<RequirementsSummary> {
  if (isMock) {
    await delay(1500)
    return MOCK_REQUIREMENTS
  }
  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${sessionId}/requirements/revise`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback }),
    },
  )
  if (!res.ok) throw new Error(`reviseRequirements failed: ${res.status}`)
  return res.json() as Promise<RequirementsSummary>
}

/* ─── Teams ───────────────────────────── */

export async function fetchTeamCandidates(
  _sessionId: string,
): Promise<{ totalCombinations: number; teams: TeamCandidate[] }> {
  if (isMock) {
    await delay(1500)
    return { totalCombinations: 1247, teams: MOCK_TEAMS }
  }
  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${_sessionId}/teams`,
  )
  if (!res.ok) throw new Error(`fetchTeamCandidates failed: ${res.status}`)
  return res.json() as Promise<{ totalCombinations: number; teams: TeamCandidate[] }>
}

export async function selectTeam(
  sessionId: string,
  teamId: string,
): Promise<void> {
  if (isMock) {
    await delay(400)
    return
  }
  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${sessionId}/teams/select`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ teamId }),
    },
  )
  if (!res.ok) throw new Error(`selectTeam failed: ${res.status}`)
}

/* ─── Stream ──────────────────────────── */

export function getStreamUrl(sessionId: string): string {
  if (isMock) return `/api/mock-stream?session_id=${sessionId}`
  const url = new URL(`${BACKEND_BASE_URL}/api/sessions/${sessionId}/stream`)
  const llmMode = process.env.NEXT_PUBLIC_SIMULATION_LLM_MODE
  if (llmMode === "stub" || llmMode === "vertex") {
    url.searchParams.set("mode", llmMode)
  }
  return url.toString()
}

/* ─── Report ──────────────────────────── */

export async function fetchReport(
  sessionId: string,
  pmPersona?: import("./types").PmPersona | null,
): Promise<Report> {
  if (isMock) return getMockReport(sessionId, pmPersona)

  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${sessionId}/report`,
  )
  if (!res.ok) {
    const detail = await errorDetail(res)
    throw new Error(detail ?? `fetchReport failed: ${res.status}`)
  }
  return res.json() as Promise<Report>
}

/* ─── Util ─────────────────────────────── */

function delay(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms))
}

async function errorDetail(res: Response): Promise<string | null> {
  try {
    const body = (await res.json()) as {
      detail?: string | { code?: string; message?: string; generationError?: string }
    }
    if (typeof body.detail === "string") return body.detail
    if (body.detail?.generationError) {
      return `${body.detail.message ?? body.detail.code}: ${body.detail.generationError}`
    }
    return body.detail?.message ?? body.detail?.code ?? null
  } catch {
    return null
  }
}
