/**
 * API 레이어
 *
 * NEXT_PUBLIC_MOCK=true 환경변수 시 mock 시나리오 반환.
 * 컴포넌트/훅은 mock 여부를 알 필요 없음 — 이 파일에서만 분기.
 */

import { BACKEND_BASE_URL } from "./constants"
import type { Report, SimulationInput } from "./types"
import { getMockReport, startMockSession } from "./mock/scenario"

const isMock = process.env.NEXT_PUBLIC_MOCK === "true"

export async function createSession(input: SimulationInput): Promise<string> {
  if (isMock) {
    return startMockSession()
  }

  const res = await fetch(`${BACKEND_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error(`createSession failed: ${res.status}`)
  const { session_id } = (await res.json()) as { session_id: string }
  return session_id
}

export function getStreamUrl(sessionId: string): string {
  if (isMock) {
    return `/api/mock-stream?session_id=${sessionId}`
  }
  return `${BACKEND_BASE_URL}/api/sessions/${sessionId}/stream`
}

export async function fetchReport(sessionId: string): Promise<Report> {
  if (isMock) {
    return getMockReport(sessionId)
  }

  const res = await fetch(
    `${BACKEND_BASE_URL}/api/sessions/${sessionId}/report`,
  )
  if (!res.ok) throw new Error(`fetchReport failed: ${res.status}`)
  return res.json() as Promise<Report>
}
