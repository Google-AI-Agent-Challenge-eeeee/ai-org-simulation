import { MessageSquare } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { MeetingSummaryItems } from "./SummaryItem"
import type { MeetingSummaryData } from "@/lib/types"

interface MeetingSummarySectionProps {
  data: MeetingSummaryData
}

export function MeetingSummarySection({ data }: MeetingSummarySectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={MessageSquare} title="킥오프 회의 요약" />
      <MeetingSummaryItems data={data} />
    </div>
  )
}
