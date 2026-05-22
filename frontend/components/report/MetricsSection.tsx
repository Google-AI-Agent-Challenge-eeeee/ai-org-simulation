import { BarChart2 } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { MetricCard } from "@/components/ui/metric-card"
import { RiskDistributionBar } from "./RiskDistributionBar"
import type { ReportMetrics } from "@/lib/types"

interface MetricsSectionProps {
  metrics: ReportMetrics
}

export function MetricsSection({ metrics }: MetricsSectionProps) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
      <SectionHeader icon={BarChart2} title="수치 평가 요약" />
      <div className="grid grid-cols-3 gap-3 mb-4">
        <MetricCard
          label="팀 핏 점수"
          value={metrics.teamFitScore}
          unit="/ 100"
          variant="success"
        />
        <MetricCard
          label="리스크 지수"
          value={metrics.riskIndex}
          sub={metrics.riskLevel}
          variant={
            metrics.riskLevel === "Low"
              ? "success"
              : metrics.riskLevel === "Mid"
                ? "warning"
                : "danger"
          }
        />
        <MetricCard
          label="예상 완료율"
          value={`${metrics.completionRate}%`}
          sub={metrics.completionLabel}
          variant="success"
        />
      </div>
      <RiskDistributionBar {...metrics.riskDistribution} />
    </div>
  )
}
