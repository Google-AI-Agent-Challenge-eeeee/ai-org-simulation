import { Avatar } from "@/components/ui/avatar"
import { ROLE_LABELS } from "@/lib/constants"
import type { Persona } from "@/lib/types"

interface PersonaChipProps {
  persona: Persona
}

export function PersonaChip({ persona }: PersonaChipProps) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <Avatar initials={persona.initials} color={persona.color} size="lg" />
      <span className="text-xs font-medium text-zinc-300">{persona.name}</span>
      <span className="text-[10px] text-zinc-500">{ROLE_LABELS[persona.role]}</span>
    </div>
  )
}
