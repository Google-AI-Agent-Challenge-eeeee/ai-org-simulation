import { Target } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { RecommendationCard } from "./RecommendationCard"
import type { Recommendation } from "@/lib/types"

interface RecommendationSectionProps {
  recommendations: Recommendation[]
}

export function RecommendationSection({ recommendations }: RecommendationSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={Target} title="권고 사항" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {recommendations.map((rec, i) => (
          <RecommendationCard key={i} recommendation={rec} />
        ))}
      </div>
    </div>
  )
}
