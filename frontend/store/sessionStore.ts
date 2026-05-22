import { create } from "zustand"
import type {
  Message,
  SessionStage,
  SimulationPhase,
  PmPersona,
  TeamCandidate,
} from "@/lib/types"

interface SessionStore {
  sessionId: string | null
  stage: SessionStage
  statusText: string
  messages: Message[]
  elapsed: number
  currentPhase: SimulationPhase | null
  backendLogs: string[]
  pmPersona: PmPersona | null
  selectedTeam: TeamCandidate | null
  requirementsAccepted: boolean

  setSessionId: (id: string) => void
  setStage: (stage: SessionStage, text?: string) => void
  appendMessage: (msg: Message) => void
  appendToken: (messageId: string, token: string) => void
  setStreaming: (messageId: string, isStreaming: boolean) => void
  setEventDone: (eventId: string) => void
  tickElapsed: () => void
  setCurrentPhase: (phase: SimulationPhase) => void
  appendBackendLog: (text: string) => void
  clearBackendLogs: () => void
  setPmPersona: (p: PmPersona) => void
  setSelectedTeam: (t: TeamCandidate) => void
  setRequirementsAccepted: (v: boolean) => void
  reset: () => void
}

const INITIAL_STATE = {
  sessionId: null,
  stage: "idle" as SessionStage,
  statusText: "",
  messages: [],
  elapsed: 0,
  currentPhase: null,
  backendLogs: [],
  pmPersona: null,
  selectedTeam: null,
  requirementsAccepted: false,
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

  // event_start 마커를 event_end(완료) 상태로 전환
  setEventDone: (eventId) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.kind === "event_start" && m.eventId === eventId
          ? { ...m, kind: "event_end" as const }
          : m,
      ),
    })),

  tickElapsed: () => set((s) => ({ elapsed: s.elapsed + 1 })),

  setCurrentPhase: (phase) => set({ currentPhase: phase }),

  appendBackendLog: (text) =>
    set((s) => ({
      backendLogs: [...s.backendLogs.slice(-9), text],
    })),

  clearBackendLogs: () => set({ backendLogs: [] }),

  setPmPersona: (p) => set({ pmPersona: p }),

  setSelectedTeam: (t) => set({ selectedTeam: t }),

  setRequirementsAccepted: (v) => set({ requirementsAccepted: v }),

  reset: () => set(INITIAL_STATE),
}))
