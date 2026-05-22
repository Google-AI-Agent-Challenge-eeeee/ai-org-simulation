import { Users } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { PersonaChip } from "./PersonaChip"
import type { Persona } from "@/lib/types"

interface TeamSectionProps {
  team: Persona[]
}

export function TeamSection({ team }: TeamSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={Users} title="구성 팀" />
      <div className="flex flex-wrap gap-6">
        {team.map((persona) => (
          <PersonaChip key={persona.id} persona={persona} />
        ))}
      </div>
    </div>
  )
}
