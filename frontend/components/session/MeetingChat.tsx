"use client"

import { motion, AnimatePresence } from "framer-motion"
import { PersonaMessage } from "./PersonaMessage"
import { EventMarker } from "./EventMarker"
import { TypingDots } from "./TypingDots"
import { useAutoScroll } from "@/hooks/useAutoScroll"
import type { Message, SessionStage } from "@/lib/types"

interface MeetingChatProps {
  messages: Message[]
  stage: SessionStage
}

const E: [number, number, number, number] = [0.25, 0.46, 0.45, 0.94]
const msgVariant = {
  hidden: { opacity: 0, y: 10, scale: 0.98 },
  show:   { opacity: 1, y: 0,  scale: 1,    transition: { duration: 0.3, ease: E } },
}

export function MeetingChat({ messages, stage }: MeetingChatProps) {
  const scrollRef = useAutoScroll(messages.length)
  const isStreaming = stage === "meeting" || stage === "team_ready" || stage === "analyzing"
  const lastMessage = messages[messages.length - 1]
  const showTyping = isStreaming && (!lastMessage || !lastMessage.isStreaming)

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-5 space-y-5">
      <AnimatePresence initial={false}>
        {messages.map((msg) => (
          <motion.div key={msg.id} variants={msgVariant} initial="hidden" animate="show">
            {msg.kind === "event_start" || msg.kind === "event_end"
              ? <EventMarker message={msg} />
              : <PersonaMessage message={msg} />
            }
          </motion.div>
        ))}
      </AnimatePresence>

      <AnimatePresence>
        {showTyping && (
          <motion.div
            key="typing"
            initial={{ opacity:0, y:8 }}
            animate={{ opacity:1, y:0 }}
            exit={{ opacity:0, y:4 }}
            transition={{ duration:0.25 }}
            className="flex gap-3 items-start"
          >
            <div className="w-9 h-9 rounded-full bg-zinc-700 flex items-center justify-center text-xs text-zinc-400 shrink-0">
              AI
            </div>
            <TypingDots />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
