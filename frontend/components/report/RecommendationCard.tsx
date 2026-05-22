import { Flame, GitMerge, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Recommendation, RecommendationType } from "@/lib/types"

const CONFIGS: Record<
  RecommendationType,
  { icon: typeof Flame; borderClass: string; iconClass: string; titleClass: string }
> = {
  burnout: {
    icon: Flame,
    borderClass: "border-l-amber-500",
    iconClass: "text-amber-400",
    titleClass: "text-amber-300",
  },
  bottleneck: {
    icon: GitMerge,
    borderClass: "border-l-orange-500",
    iconClass: "text-orange-400",
    titleClass: "text-orange-300",
  },
  turnover: {
    icon: TrendingDown,
    borderClass: "border-l-red-500",
    iconClass: "text-red-400",
    titleClass: "text-red-300",
  },
}

interface RecommendationCardProps {
  recommendation: Recommendation
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const { icon: Icon, borderClass, iconClass, titleClass } =
    CONFIGS[recommendation.type]

  return (
    <div
      className={cn(
        "rounded-lg bg-zinc-800/60 border border-zinc-700 border-l-4 p-4",
        borderClass,
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className={cn("w-4 h-4 shrink-0", iconClass)} />
        <p className={cn("text-sm font-semibold", titleClass)}>
          {recommendation.title}
        </p>
      </div>
      <p className="text-sm text-zinc-400 leading-relaxed">{recommendation.body}</p>
    </div>
  )
}
