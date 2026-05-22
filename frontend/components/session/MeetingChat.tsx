"use client"

import { PersonaMessage } from "./PersonaMessage"
import { TypingDots } from "./TypingDots"
import { useAutoScroll } from "@/hooks/useAutoScroll"
import type { Message, SessionStage } from "@/lib/types"

interface MeetingChatProps {
  messages: Message[]
  stage: SessionStage
}

export function MeetingChat({ messages, stage }: MeetingChatProps) {
  const scrollRef = useAutoScroll(messages.length)
  const isStreaming = stage === "meeting" || stage === "team_ready" || stage === "analyzing"
  const lastMessage = messages[messages.length - 1]
  const showTyping = isStreaming && (!lastMessage || !lastMessage.isStreaming)

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-5 space-y-5"
    >
      {messages.map((msg) => (
        <PersonaMessage key={msg.id} message={msg} />
      ))}
      {showTyping && (
        <div className="flex gap-3 items-start">
          <div className="w-9 h-9 rounded-full bg-zinc-700 flex items-center justify-center text-xs text-zinc-400 shrink-0">
            AI
          </div>
          <TypingDots />
        </div>
      )}
    </div>
  )
}
