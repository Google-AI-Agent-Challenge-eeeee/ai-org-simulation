import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

interface SectionHeaderProps {
  icon: LucideIcon
  title: string
  className?: string
}

export function SectionHeader({ icon: Icon, title, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex items-center gap-2 mb-4", className)}>
      <Icon className="w-4 h-4 text-zinc-400" />
      <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wide">
        {title}
      </h2>
    </div>
  )
}
