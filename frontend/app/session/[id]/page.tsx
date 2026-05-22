"use client"

import { use } from "react"
import { SessionHeader } from "@/components/session/SessionHeader"
import { StatusBar } from "@/components/session/StatusBar"
import { MeetingChat } from "@/components/session/MeetingChat"
import { SessionFooter } from "@/components/layout/SessionFooter"
import { useKickoff } from "@/hooks/useKickoff"
import { useSessionStore } from "@/store/sessionStore"

interface Props {
  params: Promise<{ id: string }>
}

export default function SessionPage({ params }: Props) {
  const { id: sessionId } = use(params)

  useKickoff(sessionId)

  const { stage, statusText, messages, elapsed } = useSessionStore()

  return (
    <div className="flex flex-col h-screen">
      <SessionHeader stage={stage} />
      <StatusBar stage={stage} statusText={statusText} elapsed={elapsed} />
      <MeetingChat messages={messages} stage={stage} />
      <SessionFooter stage={stage} sessionId={sessionId} />
    </div>
  )
}
