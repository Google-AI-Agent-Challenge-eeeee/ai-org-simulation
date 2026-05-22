import { PersonaAvatar, PersonaNameRow } from "./PersonaAvatar"
import { MessageBubble } from "./MessageBubble"
import { cn } from "@/lib/utils"
import type { Message } from "@/lib/types"

interface PersonaMessageProps {
  message: Message
}

const TURN_TYPE_LABELS: Record<
  NonNullable<Message["turnType"]>,
  { label: string; color: string }
> = {
  initiative:     { label: "Initiative",     color: "bg-indigo-500/20 border-indigo-500/30 text-indigo-300" },
  observation:    { label: "Observation",    color: "bg-zinc-700/60 border-zinc-600 text-zinc-400" },
  concern:        { label: "Concern",        color: "bg-amber-500/20 border-amber-500/30 text-amber-300" },
  dependency:     { label: "Dependency",     color: "bg-blue-500/20 border-blue-500/30 text-blue-300" },
  proposed_action:{ label: "Proposed",       color: "bg-emerald-500/20 border-emerald-500/30 text-emerald-300" },
}

export function PersonaMessage({ message }: PersonaMessageProps) {
  const turnMeta = message.turnType ? TURN_TYPE_LABELS[message.turnType] : null

  return (
    <div className="flex gap-3">
      <PersonaAvatar persona={message.persona} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <PersonaNameRow persona={message.persona} />
          {turnMeta && (
            <span
              className={cn(
                "text-[10px] px-2 py-0.5 rounded-full border font-medium",
                turnMeta.color,
              )}
            >
              {turnMeta.label}
            </span>
          )}
        </div>
        <MessageBubble content={message.content} isStreaming={message.isStreaming} />
      </div>
    </div>
  )
}
