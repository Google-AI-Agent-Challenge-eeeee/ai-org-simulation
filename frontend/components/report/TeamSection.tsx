import { Users } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { PersonaChip } from "./PersonaChip"
import type { Persona, PmPersona } from "@/lib/types"

interface TeamSectionProps {
  team: Persona[]
  pmPersona?: PmPersona
  selectedTeam?: {
    rank: number
    teamFitScore: number
    teamName?: string
  }
}

export function TeamSection({ team, pmPersona, selectedTeam }: TeamSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <div className="flex items-center justify-between mb-4">
        <SectionHeader icon={Users} title="구성 팀" className="mb-0" />
        {selectedTeam && (
          <span className="text-xs bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 px-2.5 py-1 rounded-full font-medium">
            #{selectedTeam.rank} · {selectedTeam.teamFitScore}점
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-6">
        {team.map((persona) => {
          const isPm = persona.role === "PM"
          return (
            <div key={persona.id} className="flex flex-col items-center gap-1">
              <PersonaChip persona={persona} />
              {isPm && pmPersona && (
                <span className="text-[10px] text-zinc-500 text-center leading-tight">
                  (사용자 페르소나)
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
