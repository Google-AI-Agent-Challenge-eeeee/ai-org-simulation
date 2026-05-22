"use client"

import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export type StepperStep =
  | "input"
  | "requirements"
  | "teams"
  | "simulation"
  | "report"

const STEPS: { id: StepperStep; label: string }[] = [
  { id: "input",        label: "입력" },
  { id: "requirements", label: "요구사항 검토" },
  { id: "teams",        label: "팀 선택" },
  { id: "simulation",   label: "시뮬레이션" },
  { id: "report",       label: "리포트" },
]

interface ProgressStepperProps {
  currentStep: StepperStep
  className?: string
}

export function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  const currentIdx = STEPS.findIndex((s) => s.id === currentStep)

  return (
    <div className={cn("flex items-center justify-center gap-0", className)}>
      {STEPS.map((step, idx) => {
        const isDone    = idx < currentIdx
        const isActive  = idx === currentIdx
        const isPending = idx > currentIdx

        return (
          <div key={step.id} className="flex items-center">
            {/* dot */}
            <div className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border transition-all",
                  isDone   && "bg-indigo-600 border-indigo-600 text-white",
                  isActive && "bg-indigo-600 border-indigo-500 text-white ring-2 ring-indigo-500/30",
                  isPending && "bg-zinc-800 border-zinc-700 text-zinc-500",
                )}
              >
                {isDone ? <Check className="w-3.5 h-3.5" /> : idx + 1}
              </div>
              <span
                className={cn(
                  "text-[10px] whitespace-nowrap font-medium",
                  isActive  ? "text-indigo-400" : "text-zinc-500",
                )}
              >
                {step.label}
              </span>
            </div>

            {/* connector */}
            {idx < STEPS.length - 1 && (
              <div
                className={cn(
                  "h-px w-10 mx-1 mb-4 transition-colors",
                  idx < currentIdx ? "bg-indigo-600" : "bg-zinc-700",
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
