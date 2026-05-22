import { PersonaAvatar, PersonaNameRow } from "./PersonaAvatar"
import { MessageBubble } from "./MessageBubble"
import type { Message } from "@/lib/types"

interface PersonaMessageProps {
  message: Message
}

export function PersonaMessage({ message }: PersonaMessageProps) {
  return (
    <div className="flex gap-3">
      <PersonaAvatar persona={message.persona} />
      <div>
        <PersonaNameRow persona={message.persona} />
        <MessageBubble content={message.content} isStreaming={message.isStreaming} />
      </div>
    </div>
  )
}
