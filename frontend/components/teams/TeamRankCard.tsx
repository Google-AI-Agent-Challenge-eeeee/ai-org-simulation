"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import type { TeamCandidate } from "@/lib/types"

interface TeamRankCardProps {
  team: TeamCandidate
  isSelected: boolean
  onSelect: (teamId: string) => void
}

const RANK_STYLE = {
  1: { bg: "bg-amber-500/10",  border: "border-amber-500/40",  badge: "bg-amber-500",  text: "#1" },
  2: { bg: "bg-zinc-500/10",   border: "border-zinc-500/40",   badge: "bg-zinc-400",   text: "#2" },
  3: { bg: "bg-orange-700/10", border: "border-orange-700/30", badge: "bg-orange-600", text: "#3" },
}
function getRankStyle(rank: number) {
  return (
    RANK_STYLE[rank as keyof typeof RANK_STYLE] ?? {
      bg: "bg-zinc-800/30",
      border: "border-zinc-700",
      badge: "bg-zinc-600",
      text: `#${rank}`,
    }
  )
}

function MiniBar({ value, color = "bg-indigo-500" }: { value: number; color?: string }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-zinc-700">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] text-zinc-400 w-7 text-right">{pct}%</span>
    </div>
  )
}

export function TeamRankCard({ team, isSelected, onSelect }: TeamRankCardProps) {
  const rankStyle = getRankStyle(team.team_rank)
  const isFirst   = team.team_rank === 1
  const [expanded, setExpanded] = useState(isFirst)

  return (
    <div
      onClick={() => onSelect(team.team_id)}
      className={cn(
        "rounded-xl border cursor-pointer transition-all",
        isSelected
          ? "border-indigo-500 bg-indigo-500/5 ring-1 ring-indigo-500/20"
          : cn(rankStyle.bg, rankStyle.border, "hover:border-zinc-600"),
      )}
    >
      {/* ── Header row ── */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* rank badge */}
        <div
          className={cn(
            "w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-white shrink-0",
            rankStyle.badge,
          )}
        >
          {rankStyle.text}
        </div>

        {/* name + badges */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-zinc-100">{team.team_name}</span>
            {team.badges?.map((b) => (
              <span
                key={b}
                className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300"
              >
                {b}
              </span>
            ))}
          </div>
          {/* member initials row (collapsed) */}
          {!expanded && (
            <div className="flex gap-1 mt-1">
              {team.members.map((m) => (
                <div
                  key={m.employee_id}
                  className={cn(
                    "w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-white",
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
        {!expanded && (
          <div className="shrink-0 text-right mr-3">
            <div className="h-0.5 w-16 bg-zinc-700 mb-1.5 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500"
                style={{ width: `${(team.team_fit_score / 100) * 100}%` }}
              />
            </div>
            <span className="text-base font-bold text-zinc-100">{team.team_fit_score}</span>
          </div>
        )}

        {/* expand toggle */}
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v) }}
          className="text-zinc-500 hover:text-zinc-300 transition-colors shrink-0"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* ── Expanded detail ── */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-zinc-800 pt-4">
          {/* score header */}
          <div className="flex items-end justify-between mb-4">
            <p className="text-xs text-zinc-500">적합도 점수</p>
            <span className="text-2xl font-bold text-zinc-100">{team.team_fit_score}</span>
          </div>

          {/* members */}
          <div className="flex gap-4 mb-4 flex-wrap">
            {team.members.map((m) => (
              <div key={m.employee_id} className="flex flex-col items-center gap-1">
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold text-white border-2",
                    m.color,
                    isSelected ? "border-indigo-400" : "border-transparent",
                  )}
                >
                  {m.initials}
                </div>
                <span className="text-[10px] text-zinc-300 whitespace-nowrap">{m.employee_name}</span>
                <span className="text-[9px] text-zinc-500 whitespace-nowrap">
                  ({m.assigned_role.replace(" Developer", "").replace(" Engineer", "")})
                </span>
              </div>
            ))}
          </div>

          {/* metrics + rationale 2-col */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* bars */}
            <div className="flex flex-col gap-2">
              <p className="text-xs font-medium text-zinc-400 mb-1">역량 커버리지</p>
              <div className="flex flex-col gap-1.5">
                <div>
                  <p className="text-[10px] text-zinc-500 mb-1">기술 커버리지</p>
                  <MiniBar value={team.skill_coverage_score} color="bg-indigo-500" />
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 mb-1">협업 경험</p>
                  <MiniBar value={team.role_coverage_score} color="bg-indigo-400" />
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 mb-1">가용성</p>
                  <MiniBar value={team.availability_score} color="bg-emerald-500" />
                </div>
              </div>
            </div>

            {/* rationale */}
            {team.rationale && (
              <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-3">
                <p className="text-[10px] font-semibold text-indigo-400 mb-1.5 flex items-center gap-1">
                  ✨ AI 분석 요약
                </p>
                <p className="text-xs text-zinc-300 leading-relaxed">{team.rationale}</p>
                {team.skill_gaps?.map((gap, i) => (
                  <span
                    key={i}
                    className="mt-2 inline-flex items-center gap-1 text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full"
                  >
                    ● {gap}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* risk flags */}
          {team.team_risk_flags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {team.team_risk_flags.map((f, i) => (
                <span
                  key={i}
                  className="text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full"
                >
                  ⚠ {f}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
