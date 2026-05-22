import { cn } from "@/lib/utils"

interface AvatarProps {
  initials: string
  color: string
  size?: "sm" | "md" | "lg"
  className?: string
}

const SIZE_MAP = {
  sm: "w-7 h-7 text-xs",
  md: "w-9 h-9 text-sm",
  lg: "w-12 h-12 text-base",
}

export function Avatar({ initials, color, size = "md", className }: AvatarProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full font-semibold text-white shrink-0",
        SIZE_MAP[size],
        color,
        className,
      )}
    >
      {initials}
    </div>
  )
}
