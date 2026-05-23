import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { TeamCandidate } from "@/lib/types"

interface SimulationSidebarProps {
  selectedTeam: TeamCandidate | null
  teamFitScore?: number
  riskLevel?: string
  phaseProgress?: number
  canViewReport?: boolean
  onViewReport?: () => void
}

export function SimulationSidebar({
  selectedTeam,
  teamFitScore = 84,
  riskLevel = "Moderate",
  phaseProgress = 0,
  canViewReport = false,
  onViewReport,
}: SimulationSidebarProps) {
  const riskColor =
    riskLevel === "Low" ? "text-emerald-400" :
    riskLevel === "Moderate" ? "text-amber-400" : "text-red-400"
  const riskLabel =
    riskLevel === "Low" ? "낮음" :
    riskLevel === "Moderate" ? "주의" : "높음"

  return (
    <aside className="flex h-full min-h-0 flex-col gap-4 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        {/* Active Team */}
        <div>
          <p className="mb-3 text-xs font-semibold text-zinc-100">
            참여 에이전트
          </p>
          {selectedTeam ? (
            <div className="flex flex-col gap-2">
              {selectedTeam.members.map((m) => (
                <div key={m.employee_id} className="flex items-center gap-3 rounded-lg bg-zinc-900/70 px-2 py-2">
                  <div
                    className={cn(
                      "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[10px] font-bold leading-none text-white whitespace-nowrap",
                      m.color,
                    )}
                  >
                    {m.employee_name}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs font-semibold text-zinc-100">{m.employee_name}</p>
                    <p className="truncate text-[10px] text-zinc-500">
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

        {/* Live Metrics */}
        <div className="mt-5 border-t border-zinc-800 pt-4">
          <p className="mb-3 text-xs font-semibold text-zinc-100">
            실시간 지표
          </p>
          <div className="flex flex-col gap-3">
            {/* Team Fit Score */}
            <div className="rounded-lg bg-zinc-900/70 px-3 py-3">
              <p className="text-[10px] text-zinc-500 mb-1">팀 핏 스코어</p>
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
            <div className="rounded-lg bg-zinc-900/70 px-3 py-3">
              <p className="text-[10px] text-zinc-500 mb-1">리스크 수준</p>
              <div className="flex items-center justify-between mb-1.5">
                <span className={cn("text-sm font-bold", riskColor)}>{riskLabel}</span>
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
            <div className="rounded-lg bg-zinc-900/70 px-3 py-3">
              <p className="text-[10px] text-zinc-500 mb-1">진행률</p>
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
      </div>

      <div className="mt-auto border-t border-zinc-800 pt-4">
        <p className="mb-2 text-[11px] font-medium text-zinc-500">
          시뮬레이션 완료 후 리포트를 확인할 수 있습니다.
        </p>
        <Button
          size="sm"
          disabled={!canViewReport}
          onClick={onViewReport}
          className={cn(
            "h-11 w-full gap-2 rounded-lg text-sm font-semibold transition-all",
            canViewReport
              ? "border border-indigo-400/40 bg-indigo-600 text-white hover:bg-indigo-500"
              : "border border-zinc-700 bg-zinc-800 text-zinc-500 opacity-70",
          )}
        >
          리포트 보기
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </aside>
  )
}
