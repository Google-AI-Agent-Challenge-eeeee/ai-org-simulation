import { cn } from "@/lib/utils"
import { ROLE_LABELS } from "@/lib/constants"
import type { RoleType } from "@/lib/types"

interface RoleBadgeProps {
  role: RoleType
  className?: string
}

const ROLE_BADGE_COLORS: Record<RoleType, string> = {
  PM: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  BE: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  WEB: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  iOS: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  Android: "bg-green-500/20 text-green-300 border-green-500/30",
  Infra: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  QA: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  DS: "bg-pink-500/20 text-pink-300 border-pink-500/30",
}

export function RoleBadge({ role, className }: RoleBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border",
        ROLE_BADGE_COLORS[role],
        className,
      )}
    >
      {ROLE_LABELS[role]}
    </span>
  )
}
