/**
 * 킥오프 회의 SSE 구독 훅
 *
 * Mock 모드: buildMockEvents()를 500ms 간격으로 순차 emit
 * Real 모드: getStreamUrl()로 SSE 연결
 */

"use client"

import { useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useSessionStore } from "@/store/sessionStore"
import { getStreamUrl } from "@/lib/api"
import { consumeSse } from "@/lib/sse"
import { STAGE_STATUS_TEXT } from "@/lib/constants"
import type { Persona, SessionStage } from "@/lib/types"

const isMock = process.env.NEXT_PUBLIC_MOCK === "true"

interface SseStatusData {
  stage: SessionStage
  text: string
}

interface SseMessageData {
  persona: Persona
  token: string
  messageId: string
}

export function useKickoff(sessionId: string) {
  const router = useRouter()
  const {
    setStage,
    appendMessage,
    appendToken,
    setStreaming,
    tickElapsed,
    messages,
  } = useSessionStore()

  const abortRef = useRef<AbortController | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    timerRef.current = setInterval(tickElapsed, 1000)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [tickElapsed])

  useEffect(() => {
    if (!sessionId) return
    abortRef.current = new AbortController()
    const { signal } = abortRef.current

    if (isMock) {
      runMock(sessionId, signal)
    } else {
      runReal(sessionId, signal)
    }

    return () => {
      abortRef.current?.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  async function runMock(_sessionId: string, signal: AbortSignal) {
    const { buildMockEvents } = await import("@/lib/mock/scenario")
    const events = buildMockEvents()
    const activeMessages = new Set<string>()

    for (const ev of events) {
      if (signal.aborted) break
      await delay(ev.event === "message" ? 30 : 800)
      if (signal.aborted) break

      if (ev.event === "status") {
        const d = ev.data as SseStatusData
        setStage(d.stage, d.text)
      } else if (ev.event === "message") {
        const d = ev.data as SseMessageData

        if (!activeMessages.has(d.messageId)) {
          activeMessages.add(d.messageId)
          appendMessage({
            id: d.messageId,
            persona: d.persona,
            content: "",
            isStreaming: true,
          })
        }
        appendToken(d.messageId, d.token)
      } else if (ev.event === "done") {
        messages.forEach((m) => setStreaming(m.id, false))
        setStage("done", STAGE_STATUS_TEXT.done)
        router.push(`/report/${_sessionId}`)
      }
    }
  }

  async function runReal(sessionId: string, signal: AbortSignal) {
    const url = getStreamUrl(sessionId)
    const activeMessages = new Set<string>()

    await consumeSse(
      url,
      (ev) => {
        if (ev.event === "status") {
          const d = ev.data as SseStatusData
          setStage(d.stage, d.text)
        } else if (ev.event === "message") {
          const d = ev.data as SseMessageData

          if (!activeMessages.has(d.messageId)) {
            activeMessages.add(d.messageId)
            appendMessage({
              id: d.messageId,
              persona: d.persona,
              content: "",
              isStreaming: true,
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
}

function delay(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}
