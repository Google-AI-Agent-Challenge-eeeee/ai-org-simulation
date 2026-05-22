interface RiskDistributionBarProps {
  safe: number
  caution: number
  danger: number
}

export function RiskDistributionBar({ safe, caution, danger }: RiskDistributionBarProps) {
  return (
    <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-4">
      <p className="text-xs text-zinc-400 mb-2">리스크 분포</p>
      <div className="flex h-2.5 rounded-full overflow-hidden gap-0.5">
        <div
          className="bg-emerald-500 rounded-l-full transition-all"
          style={{ width: `${safe}%` }}
        />
        <div
          className="bg-amber-400 transition-all"
          style={{ width: `${caution}%` }}
        />
        <div
          className="bg-red-500 rounded-r-full transition-all"
          style={{ width: `${danger}%` }}
        />
      </div>
      <div className="flex justify-between mt-1.5 text-[10px] text-zinc-500">
        <span>안전 ({safe}%)</span>
        <span>주의 ({caution}%)</span>
        <span>위험 ({danger}%)</span>
      </div>
    </div>
  )
}
