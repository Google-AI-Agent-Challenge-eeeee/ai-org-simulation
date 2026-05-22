import { cn } from "@/lib/utils"

interface MetricCardProps {
  label: string
  value: number | string
  unit?: string
  sub?: string
  variant?: "default" | "success" | "warning" | "danger"
  className?: string
}

const VARIANT_COLORS = {
  default: "text-white",
  success: "text-emerald-400",
  warning: "text-amber-400",
  danger: "text-red-400",
}

export function MetricCard({
  label,
  value,
  unit,
  sub,
  variant = "default",
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 rounded-lg bg-zinc-800/60 border border-zinc-700 p-4",
        className,
      )}
    >
      <span className="text-xs text-zinc-400">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className={cn("text-3xl font-bold", VARIANT_COLORS[variant])}>
          {value}
        </span>
        {unit && (
          <span className="text-sm text-zinc-400">{unit}</span>
        )}
      </div>
      {sub && <span className="text-xs text-zinc-500">{sub}</span>}
    </div>
  )
}
