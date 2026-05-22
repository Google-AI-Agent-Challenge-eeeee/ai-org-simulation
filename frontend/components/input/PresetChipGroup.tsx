"use client"

import { PresetChip } from "@/components/ui/preset-chip"
import type { PmStylePreset } from "@/lib/constants"
import { PM_STYLE_PRESETS } from "@/lib/constants"

interface PresetChipGroupProps {
  selected: PmStylePreset
  onChange: (id: PmStylePreset) => void
}

export function PresetChipGroup({ selected, onChange }: PresetChipGroupProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {PM_STYLE_PRESETS.map((preset) => (
        <PresetChip
          key={preset.id}
          label={preset.label}
          selected={selected === preset.id}
          onClick={() => onChange(preset.id)}
        />
      ))}
    </div>
  )
}
