import { AlertTriangle, Zap, TrendingDown, Shield } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Recommendation } from "@/lib/types"

interface RecommendationCardProps {
  recommendation: Recommendation
}

const TYPE_CONFIG = {
  burnout: {
    icon: TrendingDown,
    border: "border-l-amber-500",
    bg: "bg-amber-500/5",
    border2: "border-amber-500/20",
    iconColor: "text-amber-400",
  },
  bottleneck: {
    icon: AlertTriangle,
    border: "border-l-red-500",
    bg: "bg-red-500/5",
    border2: "border-red-500/20",
    iconColor: "text-red-400",
  },
  turnover: {
    icon: Zap,
    border: "border-l-orange-500",
    bg: "bg-orange-500/5",
    border2: "border-orange-500/20",
    iconColor: "text-orange-400",
  },
  security: {
    icon: Shield,
    border: "border-l-yellow-500",
    bg: "bg-yellow-500/5",
    border2: "border-yellow-500/20",
    iconColor: "text-yellow-400",
  },
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const cfg = TYPE_CONFIG[recommendation.type] ?? TYPE_CONFIG.bottleneck
  const Icon = cfg.icon

  return (
    <div
      className={cn(
        "rounded-xl border border-l-4 p-4 flex flex-col gap-2",
        cfg.border,
        cfg.bg,
        cfg.border2,
      )}
    >
      <div className="flex items-center gap-2">
        <Icon className={cn("w-4 h-4 shrink-0", cfg.iconColor)} />
        <h3 className="text-sm font-semibold text-zinc-100">{recommendation.title}</h3>
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed">{recommendation.body}</p>
      <button
        type="button"
        className={cn("text-xs font-medium text-left mt-1 hover:underline", cfg.iconColor)}
      >
        상세 분석 보기 →
      </button>
    </div>
  )
}
