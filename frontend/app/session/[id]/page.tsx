"use client"

import { use } from "react"
import { motion } from "framer-motion"
import { SessionHeader } from "@/components/session/SessionHeader"
import { StatusBar } from "@/components/session/StatusBar"
import { MeetingChat } from "@/components/session/MeetingChat"
import { SessionFooter } from "@/components/layout/SessionFooter"
import { useKickoff } from "@/hooks/useKickoff"
import { useSessionStore } from "@/store/sessionStore"
import { fadeDown } from "@/lib/motion"

interface Props {
  params: Promise<{ id: string }>
}

export default function SessionPage({ params }: Props) {
  const { id: sessionId } = use(params)

  useKickoff(sessionId)

  const { stage, statusText, messages, elapsed } = useSessionStore()

  return (
    <div className="flex flex-col h-screen">
      <motion.div initial="hidden" animate="show" variants={fadeDown}>
        <SessionHeader stage={stage} />
        <StatusBar stage={stage} statusText={statusText} elapsed={elapsed} />
      </motion.div>

      <MeetingChat messages={messages} stage={stage} />

      <motion.div
        initial={{ opacity:0, y:12 }}
        animate={{ opacity:1, y:0 }}
        transition={{ duration:0.4, delay:0.2, ease:[0.25,0.46,0.45,0.94] as [number,number,number,number] }}
      >
        <SessionFooter stage={stage} sessionId={sessionId} />
      </motion.div>
    </div>
  )
}
