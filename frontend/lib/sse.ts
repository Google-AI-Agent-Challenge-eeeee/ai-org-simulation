/**
 * SSE 스트림 파싱 유틸
 *
 * FastAPI StreamingResponse 형식:
 *   event: <type>\n
 *   data: <json>\n\n
 */

export interface SseEvent<T = unknown> {
  event: string
  data: T
}

type SseHandler<T = unknown> = (event: SseEvent<T>) => void

export async function consumeSse<T = unknown>(
  url: string,
  onEvent: SseHandler<T>,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(url, { signal })
  if (!res.ok || !res.body) {
    throw new Error(`SSE fetch failed: ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split("\n\n")
    buffer = parts.pop() ?? ""

    for (const part of parts) {
      const lines = part.split("\n")
      let eventType = "message"
      let dataLine = ""

      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim()
        } else if (line.startsWith("data:")) {
          dataLine = line.slice(5).trim()
        }
      }

      if (!dataLine) continue
      try {
        const parsed = JSON.parse(dataLine) as T
        onEvent({ event: eventType, data: parsed })
      } catch {
        // non-JSON data — skip
      }
    }
  }
}
