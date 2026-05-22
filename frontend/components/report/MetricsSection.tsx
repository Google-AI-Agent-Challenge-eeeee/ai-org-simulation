import { BarChart2 } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { MetricCard } from "@/components/ui/metric-card"
import type { ReportMetrics } from "@/lib/types"
import { cn } from "@/lib/utils"

interface MetricsSectionProps {
  metrics: ReportMetrics
}

function RiskDistributionBar({
  technical,
  resource,
  timeline,
}: {
  technical: number
  resource: number
  timeline: number
}) {
  const total = technical + resource + timeline
  const techPct     = Math.round((technical / total) * 100)
  const resourcePct = Math.round((resource / total) * 100)
  const timelinePct = 100 - techPct - resourcePct

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-zinc-500">Risk Distribution</span>
        <span className="text-xs text-zinc-500">Total: {metrics_total(technical, resource, timeline)}%</span>
      </div>
      <div className="h-2 rounded-full overflow-hidden flex">
        <div className="bg-indigo-500 transition-all" style={{ width: `${techPct}%` }} />
        <div className="bg-amber-500 transition-all" style={{ width: `${resourcePct}%` }} />
        <div className="bg-zinc-500 transition-all" style={{ width: `${timelinePct}%` }} />
      </div>
      <div className="flex gap-4 mt-1.5">
        {[
          { label: "Technical",  color: "bg-indigo-500", pct: techPct },
          { label: "Resource",   color: "bg-amber-500",  pct: resourcePct },
          { label: "Timeline",   color: "bg-zinc-500",   pct: timelinePct },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1">
            <span className={cn("w-2 h-2 rounded-full", item.color)} />
            <span className="text-[10px] text-zinc-500">{item.label} ({item.pct}%)</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function metrics_total(a: number, b: number, c: number) {
  return a + b + c
}

export function MetricsSection({ metrics }: MetricsSectionProps) {
  const confidenceColor =
    metrics.confidenceLevel === "High" ? "text-emerald-400" :
    metrics.confidenceLevel === "Mid"  ? "text-amber-400"   : "text-red-400"

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <div className="flex items-center justify-between mb-4">
        <SectionHeader icon={BarChart2} title="수치 평가 요약" className="mb-0" />
        {metrics.confidenceLevel && (
          <span className={cn("text-xs font-medium", confidenceColor)}>
            Confidence Level: {metrics.confidenceLevel}
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <MetricCard
          label="Fit Score"
          value={metrics.teamFitScore}
          unit="/ 100"
          variant="success"
        />
        <MetricCard
          label="Risk Index"
          value={`${metrics.riskIndex}%`}
          variant={
            metrics.riskLevel === "Low" ? "success" :
            metrics.riskLevel === "Mid" ? "warning" : "danger"
          }
        />
        <MetricCard
          label="Completion Rate"
          value={`${metrics.completionRate}%`}
          variant="success"
        />
      </div>

      <RiskDistributionBar
        technical={metrics.riskDistribution.technical}
        resource={metrics.riskDistribution.resource}
        timeline={metrics.riskDistribution.timeline}
      />
    </div>
  )
}
