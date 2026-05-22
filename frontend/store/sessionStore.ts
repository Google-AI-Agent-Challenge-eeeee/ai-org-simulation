import { create } from "zustand"
import type { Message, SessionStage } from "@/lib/types"

interface SessionStore {
  sessionId: string | null
  stage: SessionStage
  statusText: string
  messages: Message[]
  elapsed: number

  setSessionId: (id: string) => void
  setStage: (stage: SessionStage, text?: string) => void
  appendMessage: (msg: Message) => void
  appendToken: (messageId: string, token: string) => void
  setStreaming: (messageId: string, isStreaming: boolean) => void
  tickElapsed: () => void
  reset: () => void
}

const INITIAL_STATE = {
  sessionId: null,
  stage: "idle" as SessionStage,
  statusText: "",
  messages: [],
  elapsed: 0,
}

export const useSessionStore = create<SessionStore>((set) => ({
  ...INITIAL_STATE,

  setSessionId: (id) => set({ sessionId: id }),

  setStage: (stage, text) =>
    set((s) => ({ stage, statusText: text ?? s.statusText })),

  appendMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  appendToken: (messageId, token) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId ? { ...m, content: m.content + token } : m,
      ),
    })),

  setStreaming: (messageId, isStreaming) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId ? { ...m, isStreaming } : m,
      ),
    })),

  tickElapsed: () => set((s) => ({ elapsed: s.elapsed + 1 })),

  reset: () => set(INITIAL_STATE),
}))
