"use client"

import { useState } from "react"
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import type { TeamCandidate } from "@/lib/types"

interface TeamRankCardProps {
  team: TeamCandidate
  isSelected: boolean
  onSelect: (teamId: string) => void
}

const RANK_STYLE = {
  1: { bg: "bg-zinc-900", border: "border-amber-500/40", badge: "bg-amber-500", text: "1위" },
  2: { bg: "bg-zinc-900", border: "border-zinc-500/40", badge: "bg-zinc-400", text: "2위" },
  3: { bg: "bg-zinc-900", border: "border-orange-700/30", badge: "bg-orange-600", text: "3위" },
}
function getRankStyle(rank: number) {
  return (
    RANK_STYLE[rank as keyof typeof RANK_STYLE] ?? {
      bg: "bg-zinc-900",
      border: "border-zinc-700",
      badge: "bg-zinc-600",
      text: `${rank}위`,
    }
  )
}

function MiniBar({ label, value, color = "bg-indigo-500" }: { label: string; value: number; color?: string }) {
  const pct = Math.round(value * 100)
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <p className="text-[11px] text-zinc-500">{label}</p>
        <span className="text-[11px] font-semibold text-zinc-300">{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-zinc-700">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function formatRole(role: string) {
  return role.replace(" Developer", "").replace(" Engineer", "")
}

function formatRiskFlag(flag: string) {
  const labels: Record<string, string> = {
    availability_risk: "가용성 리스크",
    skill_gap: "스킬 갭",
    workload_risk: "업무량 리스크",
    collaboration_risk: "협업 리스크",
  }
  return labels[flag] ?? flag.replaceAll("_", " ")
}

export function TeamRankCard({ team, isSelected, onSelect }: TeamRankCardProps) {
  const rankStyle = getRankStyle(team.team_rank)
  const isFirst   = team.team_rank === 1
  const [expanded, setExpanded] = useState(isFirst)

  return (
    <div
      onClick={() => onSelect(team.team_id)}
      className={cn(
        "rounded-xl border cursor-pointer overflow-hidden transition-all",
        isSelected
          ? "border-indigo-500 bg-zinc-900 ring-1 ring-indigo-500/30"
          : cn(rankStyle.bg, rankStyle.border, "hover:border-zinc-600"),
      )}
    >
      {/* ── Header row ── */}
      <div className="flex items-center gap-4 px-5 py-4">
        {/* rank badge */}
        <div
          className={cn(
            "h-8 rounded-lg px-3 flex items-center justify-center text-xs font-bold text-white shrink-0",
            rankStyle.badge,
          )}
        >
          {rankStyle.text}
        </div>

        {/* name + badges */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="truncate font-semibold text-base text-zinc-100">{team.team_name}</span>
            {isSelected && (
              <span
                className="shrink-0 text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300"
              >
                선택됨
              </span>
            )}
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            적합도와 가용성을 기준으로 정렬된 추천 팀입니다.
          </p>
          {/* member initials row (collapsed) */}
          {!expanded && (
            <div className="flex gap-1.5 mt-2">
              {team.members.map((m) => (
                <div
                  key={m.employee_id}
                  className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white",
                    m.color,
                  )}
                  title={`${m.employee_name} (${m.assigned_role})`}
                >
                  {m.initials[0]}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* score */}
        <div className="hidden shrink-0 text-right sm:block">
          <p className="text-[10px] text-zinc-500">적합도</p>
          <span className="text-xl font-bold text-zinc-100">{team.team_fit_score}</span>
        </div>

        {/* expand toggle */}
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v) }}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
          aria-label={expanded ? "팀 상세 접기" : "팀 상세 펼치기"}
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* ── Expanded detail ── */}
      {expanded && (
        <div className="px-5 pb-5 border-t border-zinc-800 pt-5">
          {/* members */}
          <div className="mb-5 flex flex-wrap gap-4">
            {team.members.map((m) => (
              <div key={m.employee_id} className="flex w-20 flex-col items-center gap-1.5 text-center">
                <div
                  className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center text-[11px] font-bold text-white ring-2 ring-zinc-700",
                    m.color,
                    isSelected && "ring-indigo-400",
                  )}
                >
                  {m.employee_name}
                </div>
                <p className="w-full text-[11px] font-semibold text-zinc-200">{m.employee_name}</p>
                <p className="w-full truncate text-[10px] text-zinc-500">{formatRole(m.assigned_role)}</p>
              </div>
            ))}
          </div>

          {/* metrics + rationale 2-col */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* bars */}
            <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-4">
              <p className="mb-3 text-xs font-semibold text-zinc-300">팀 적합도 지표</p>
              <div className="flex flex-col gap-3">
                <MiniBar label="기술 커버리지" value={team.skill_coverage_score} color="bg-indigo-500" />
                <MiniBar label="역할 커버리지" value={team.role_coverage_score} color="bg-indigo-400" />
                <MiniBar label="가용성" value={team.availability_score} color="bg-emerald-500" />
              </div>
            </div>

            {/* rationale */}
            {team.rationale && (
              <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-4">
                <p className="text-xs font-semibold text-zinc-300 mb-2">추천 근거</p>
                <p className="text-xs text-zinc-300 leading-relaxed">{team.rationale}</p>
                {team.skill_gaps?.map((gap, i) => (
                  <span
                    key={i}
                    className="mt-2 inline-flex items-center gap-1 text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full"
                  >
                    {gap}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* risk flags */}
          {team.team_risk_flags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {team.team_risk_flags.map((f, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 rounded-full border border-red-300/60 bg-red-500/25 px-2.5 py-1 text-xs font-semibold text-red-400"
                >
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                  {formatRiskFlag(f)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
