/**
 * 5-phase 시뮬레이션 SSE 구독 훅
 *
 * Mock 모드: buildMockEvents()를 인터벌로 순차 emit
 * Real 모드: SSE getStreamUrl()로 연결
 */
"use client"

import { useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useSessionStore } from "@/store/sessionStore"
import { getStreamUrl } from "@/lib/api"
import { consumeSse } from "@/lib/sse"
import { STAGE_STATUS_TEXT } from "@/lib/constants"
import type { Persona, SessionStage, SimulationPhase, Message } from "@/lib/types"

const isMock = process.env.NEXT_PUBLIC_MOCK === "true"

interface SseStatusData {
  stage: SessionStage
  text: string
  phase?: SimulationPhase
  phaseIndex?: number
}

interface SseMessageData {
  persona: Persona
  token: string
  messageId: string
  turnType?: Message["turnType"]
}

interface SseBackendLogData {
  text: string
}

interface SseEventStartData { eventId: string; description: string }
interface SseEventEndData   { eventId: string }

// 이벤트 마커용 시스템 페르소나 (채팅 버블 없이 구분선으로 렌더링됨)
const SYSTEM_PERSONA = {
  id: "__system__",
  name: "System",
  role: "PM" as const,
  color: "bg-zinc-700",
  initials: "SY",
}

export function useSimulation(sessionId: string) {
  const router = useRouter()
  const {
    setStage,
    appendMessage,
    appendToken,
    setStreaming,
    setEventDone,
    tickElapsed,
    setCurrentPhase,
    appendBackendLog,
    clearBackendLogs,
    messages,
    pmPersona,
  } = useSessionStore()

  const abortRef = useRef<AbortController | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    timerRef.current = setInterval(tickElapsed, 1000)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [tickElapsed])

  async function runMock(_sessionId: string, signal: AbortSignal) {
    const { buildMockEvents } = await import("@/lib/mock/scenario")
    const events = buildMockEvents(pmPersona)
    const activeMessages = new Set<string>()

    for (const ev of events) {
      if (signal.aborted) break

      if (ev.event === "status") {
        const d = ev.data as SseStatusData
        setStage(d.stage, d.text)
        if (d.phase) setCurrentPhase(d.phase)
        await delay(900)
      } else if (ev.event === "event_start") {
        const d = ev.data as SseEventStartData
        appendMessage({
          id:               `evt_${d.eventId}`,
          persona:          SYSTEM_PERSONA,
          content:          d.description,
          isStreaming:      true,
          kind:             "event_start",
          eventId:          d.eventId,
          eventDescription: d.description,
        })
        await delay(300)
      } else if (ev.event === "event_end") {
        const d = ev.data as SseEventEndData
        setEventDone(d.eventId)
        await delay(300)
      } else if (ev.event === "backend_log") {
        const d = ev.data as SseBackendLogData
        appendBackendLog(d.text)
        await delay(200)
      } else if (ev.event === "message") {
        const d = ev.data as SseMessageData

        if (!activeMessages.has(d.messageId)) {
          activeMessages.add(d.messageId)
          appendMessage({
            id: d.messageId,
            persona: d.persona,
            content: "",
            isStreaming: true,
            turnType: d.turnType,
          })
        }
        appendToken(d.messageId, d.token)
        await delay(22)
      } else if (ev.event === "done") {
        messages.forEach((m) => setStreaming(m.id, false))
        setStage("done", STAGE_STATUS_TEXT.done)
        await delay(800)
        router.push(`/report/${_sessionId}`)
      }
    }
  }

  async function runReal(sessionId: string, signal: AbortSignal) {
    const url = getStreamUrl(sessionId)
    const activeMessages = new Set<string>()

    await consumeSse(
      url,
      async (ev) => {
        if (ev.event === "status") {
          const d = ev.data as SseStatusData
          setStage(d.stage, d.text)
          if (d.phase) setCurrentPhase(d.phase)
        } else if (ev.event === "backend_log") {
          const d = ev.data as SseBackendLogData
          appendBackendLog(d.text)
        } else if (ev.event === "event_start") {
          const d = ev.data as SseEventStartData
          appendMessage({
            id:               `evt_${d.eventId}`,
            persona:          SYSTEM_PERSONA,
            content:          d.description,
            isStreaming:      true,
            kind:             "event_start",
            eventId:          d.eventId,
            eventDescription: d.description,
          })
        } else if (ev.event === "event_end") {
          const d = ev.data as SseEventEndData
          setEventDone(d.eventId)
        } else if (ev.event === "message") {
          const d = ev.data as SseMessageData
          if (!activeMessages.has(d.messageId)) {
            activeMessages.add(d.messageId)
            appendMessage({
              id: d.messageId,
              persona: d.persona,
              content: "",
              isStreaming: true,
              turnType: d.turnType,
            })
          }
          appendToken(d.messageId, d.token)
        } else if (ev.event === "done") {
          setStage("done", STAGE_STATUS_TEXT.done)
          router.push(`/report/${sessionId}`)
        }
      },
      signal,
    )
  }

  useEffect(() => {
    if (!sessionId) return
    clearBackendLogs()
    abortRef.current = new AbortController()
    const { signal } = abortRef.current

    const swallowAbort = (e: unknown) => {
      if ((e as { name?: string })?.name !== "AbortError") throw e
    }

    if (isMock) {
      runMock(sessionId, signal).catch(swallowAbort)
    } else {
      runReal(sessionId, signal).catch(swallowAbort)
    }

    return () => abortRef.current?.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])
}

function delay(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms))
}
