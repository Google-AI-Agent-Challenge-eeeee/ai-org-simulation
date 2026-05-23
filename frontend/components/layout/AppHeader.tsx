"use client"

import { Cpu, Link, Download, LayoutDashboard, FlaskConical, Bot, FileBarChart } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface AppHeaderProps {
  reportTitle?: string
  reportCreatedAt?: string
  reportId?: string
  projectName?: string
  onCopyLink?: () => void
  onDownloadPdf?: () => void
}

const NAV_ITEMS = [
  { label: "Dashboard",    icon: LayoutDashboard },
  { label: "Simulations",  icon: FlaskConical },
  { label: "Agents",       icon: Bot },
  { label: "Report",       icon: FileBarChart, active: true },
]

export function AppHeader({
  reportTitle,
  reportCreatedAt,
  reportId,
  projectName,
  onCopyLink,
  onDownloadPdf,
}: AppHeaderProps) {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950">
      {/* top nav */}
      <div className="flex items-center gap-6 px-6 py-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-bold text-zinc-100">AI Org Simulation</span>
        </div>

        <nav className="flex items-center gap-1 flex-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.label}
              type="button"
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors",
                item.active
                  ? "text-indigo-400 font-semibold"
                  : "text-zinc-400 hover:text-zinc-200",
              )}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-2 shrink-0 no-print">
          <Button
            variant="outline"
            size="sm"
            onClick={onCopyLink}
            className="gap-1.5 border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-xs"
          >
            <Link className="w-3.5 h-3.5" />
            Copy Link
          </Button>
          <Button
            size="sm"
            onClick={onDownloadPdf}
            className="gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            PDF
          </Button>
        </div>
      </div>

      {/* report title row */}
      {reportTitle && (
        <div className="flex items-start gap-4 px-6 pb-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-zinc-100">{reportTitle}</h1>
            {(reportId || projectName) && (
              <p className="text-xs text-zinc-500 mt-0.5">
                {reportId && <span>ID: {reportId}</span>}
                {reportId && projectName && <span> · </span>}
                {projectName && <span>{projectName}</span>}
              </p>
            )}
            {reportCreatedAt && (
              <p className="text-xs text-zinc-600 mt-0.5">{reportCreatedAt}</p>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
