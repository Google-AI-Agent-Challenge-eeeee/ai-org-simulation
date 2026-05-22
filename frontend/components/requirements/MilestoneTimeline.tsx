import type { Milestone } from "@/lib/types"

interface MilestoneTimelineProps {
  milestones: Milestone[]
}

export function MilestoneTimeline({ milestones }: MilestoneTimelineProps) {
  return (
    <div className="relative flex items-start justify-between px-2">
      {/* connecting line */}
      <div className="absolute top-2.5 left-6 right-6 h-px bg-zinc-700" />

      {milestones.map((m, i) => (
        <div key={i} className="relative flex flex-col items-center gap-1 z-10">
          <div
            className={`w-5 h-5 rounded-full border-2 ${
              i === 0 ? "bg-indigo-600 border-indigo-500" : "bg-zinc-800 border-zinc-600"
            }`}
          />
          <span className="text-[11px] font-medium text-zinc-300 whitespace-nowrap">{m.label}</span>
          <span className="text-[10px] text-zinc-500">Day {m.day}</span>
        </div>
      ))}
    </div>
  )
}
