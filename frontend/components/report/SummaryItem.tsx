import { CheckCircle, AlertTriangle, Circle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { MeetingSummaryData } from "@/lib/types"

type SummaryType = "decision" | "issue" | "discussion"

interface SummaryItemProps {
  type: SummaryType
  title: string
  items: string[]
}

const CONFIGS: Record<
  SummaryType,
  { icon: typeof CheckCircle; iconClass: string; titleClass: string }
> = {
  decision: {
    icon: CheckCircle,
    iconClass: "text-emerald-400",
    titleClass: "text-emerald-300",
  },
  issue: {
    icon: AlertTriangle,
    iconClass: "text-amber-400",
    titleClass: "text-amber-300",
  },
  discussion: {
    icon: Circle,
    iconClass: "text-blue-400",
    titleClass: "text-blue-300",
  },
}

export function SummaryItem({ type, title, items }: SummaryItemProps) {
  const { icon: Icon, iconClass, titleClass } = CONFIGS[type]

  return (
    <div className="flex gap-3">
      <Icon className={cn("w-4 h-4 mt-0.5 shrink-0", iconClass)} />
      <div>
        <p className={cn("text-sm font-semibold mb-1", titleClass)}>{title}</p>
        <ul className="space-y-1">
          {items.map((item, i) => (
            <li key={i} className="text-sm text-zinc-400 leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

interface MeetingSummarySectionProps {
  data: MeetingSummaryData
}

export function MeetingSummaryItems({ data }: MeetingSummarySectionProps) {
  return (
    <div className="space-y-5">
      <SummaryItem type="decision" title="합의된 결정사항" items={data.decisions} />
      <SummaryItem type="issue" title="발생한 이슈" items={data.issues} />
      <SummaryItem type="discussion" title="주요 논의 포인트" items={data.discussions} />
    </div>
  )
}
