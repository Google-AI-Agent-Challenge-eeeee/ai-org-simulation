"use client"

import { cn } from "@/lib/utils"

interface Tab {
  id: string
  label: string
}

interface TabGroupProps {
  tabs: Tab[]
  activeTab: string
  onChange: (id: string) => void
}

export function TabGroup({ tabs, activeTab, onChange }: TabGroupProps) {
  return (
    <div className="flex gap-4 border-b border-zinc-700 mb-4">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={cn(
            "pb-2 text-sm font-medium transition-colors",
            activeTab === tab.id
              ? "border-b-2 border-indigo-500 text-indigo-400"
              : "text-zinc-400 hover:text-zinc-200",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
