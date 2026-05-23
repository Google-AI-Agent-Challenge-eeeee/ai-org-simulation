import { Avatar } from "@/components/ui/avatar"
import { RoleBadge } from "@/components/ui/role-badge"
import type { Persona } from "@/lib/types"

interface PersonaAvatarProps {
  persona: Persona
}

export function PersonaAvatar({ persona }: PersonaAvatarProps) {
  return (
    <div className="flex flex-col items-center gap-1 shrink-0">
      <Avatar initials={persona.name} color={persona.color} size="md" className="text-[10px]" />
    </div>
  )
}

export function PersonaNameRow({ persona }: PersonaAvatarProps) {
  return (
    <div className="flex items-center gap-2 mb-1">
      <span className="text-sm font-semibold text-zinc-200">{persona.name}</span>
      <RoleBadge role={persona.role} />
    </div>
  )
}
