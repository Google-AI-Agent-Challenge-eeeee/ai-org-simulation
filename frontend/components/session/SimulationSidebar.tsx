import { cn } from "@/lib/utils"
import type { TeamCandidate } from "@/lib/types"

interface SimulationSidebarProps {
  selectedTeam: TeamCandidate | null
  teamFitScore?: number
  riskLevel?: string
  phaseProgress?: number
}

export function SimulationSidebar({
  selectedTeam,
  teamFitScore = 84,
  riskLevel = "Moderate",
  phaseProgress = 0,
}: SimulationSidebarProps) {
  const riskColor =
    riskLevel === "Low" ? "text-emerald-400" :
    riskLevel === "Moderate" ? "text-amber-400" : "text-red-400"

  return (
    <aside className="w-56 shrink-0 hidden lg:flex flex-col gap-4 p-4 border-l border-zinc-800 bg-zinc-950/50">
      {/* Active Team */}
      <div>
        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">
          Active Team
        </p>
        {selectedTeam ? (
          <div className="flex flex-col gap-2">
            {selectedTeam.members.map((m) => (
              <div key={m.employee_id} className="flex items-center gap-2">
                <div
                  className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0",
                    m.color,
                  )}
                >
                  {m.initials}
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-zinc-200 truncate">{m.employee_name}</p>
                  <p className="text-[10px] text-zinc-500 truncate">
                    {m.assigned_role.replace(" Developer", "").replace(" Engineer", "")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-zinc-500">팀 미선택</p>
        )}
      </div>

      <div className="border-t border-zinc-800" />

      {/* Live Metrics */}
      <div>
        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">
          Live Metrics
        </p>
        <div className="flex flex-col gap-3">
          {/* Team Fit Score */}
          <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-3">
            <p className="text-[10px] text-zinc-500 mb-1">Team Fit Score</p>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-bold text-zinc-100">{teamFitScore}%</span>
            </div>
            <div className="h-1 rounded-full bg-zinc-700">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-700"
                style={{ width: `${teamFitScore}%` }}
              />
            </div>
          </div>

          {/* Risk Level */}
          <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-3">
            <p className="text-[10px] text-zinc-500 mb-1">Risk Level</p>
            <div className="flex items-center justify-between mb-1.5">
              <span className={cn("text-sm font-bold", riskColor)}>{riskLevel}</span>
            </div>
            <div className="h-1 rounded-full bg-zinc-700">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-700",
                  riskLevel === "Low" ? "bg-emerald-500" :
                  riskLevel === "Moderate" ? "bg-amber-500" : "bg-red-500",
                )}
                style={{ width: riskLevel === "Low" ? "25%" : riskLevel === "Moderate" ? "55%" : "85%" }}
              />
            </div>
          </div>

          {/* Phase Progress */}
          <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-3">
            <p className="text-[10px] text-zinc-500 mb-1">Phase Progress</p>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-bold text-zinc-100">{phaseProgress}%</span>
            </div>
            <div className="h-1 rounded-full bg-zinc-700">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                style={{ width: `${phaseProgress}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
