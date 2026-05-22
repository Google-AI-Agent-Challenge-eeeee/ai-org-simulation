import { cn } from "@/lib/utils"

interface PresetChipProps {
  label: string
  selected: boolean
  onClick: () => void
  className?: string
}

export function PresetChip({ label, selected, onClick, className }: PresetChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "px-4 py-1.5 rounded-full text-sm font-medium border transition-colors",
        selected
          ? "bg-indigo-600 border-indigo-600 text-white"
          : "bg-transparent border-zinc-600 text-zinc-400 hover:border-zinc-400 hover:text-zinc-200",
        className,
      )}
    >
      {label}
    </button>
  )
}
