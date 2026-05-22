"use client"

import { motion } from "framer-motion"
import type { Message } from "@/lib/types"

interface EventMarkerProps {
  message: Message
}

export function EventMarker({ message }: EventMarkerProps) {
  const isDone = message.kind === "event_end"

  return (
    <div className="flex items-center gap-3 py-1 select-none">
      {/* 왼쪽 구분선 */}
      <div className="flex-1 h-px bg-zinc-700/60" />

      {/* 중앙 배지 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.25 }}
        className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap border
          ${isDone
            ? "bg-emerald-950/40 border-emerald-700/40 text-emerald-400"
            : "bg-zinc-800/70 border-zinc-600/40 text-zinc-300"
          }`}
      >
        {isDone ? (
          <>
            {/* 완료 아이콘 */}
            <svg className="w-3 h-3 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-emerald-300/90">{message.eventDescription}</span>
            <span className="text-emerald-600 font-normal">완료</span>
          </>
        ) : (
          <>
            {/* 스피너 */}
            <motion.span
              className="w-2.5 h-2.5 rounded-full border-2 border-zinc-500 border-t-zinc-200 shrink-0"
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
              style={{ display: "inline-block" }}
            />
            <span className="text-zinc-200/90">{message.eventDescription}</span>
            <span className="text-zinc-500 font-normal">generating…</span>
          </>
        )}
      </motion.div>

      {/* 오른쪽 구분선 */}
      <div className="flex-1 h-px bg-zinc-700/60" />
    </div>
  )
}
