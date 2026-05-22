"use client"

import { use } from "react"
import { motion } from "framer-motion"
import { AppHeader } from "@/components/layout/AppHeader"
import { TeamSection } from "@/components/report/TeamSection"
import { MetricsSection } from "@/components/report/MetricsSection"
import { MeetingSummarySection } from "@/components/report/MeetingSummarySection"
import { RecommendationSection } from "@/components/report/RecommendationSection"
import { useReport } from "@/hooks/useReport"
import { fadeDown, fadeUp, staggerContainer } from "@/lib/motion"

interface Props {
  params: Promise<{ id: string }>
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("ko-KR", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  })
}

export default function ReportPage({ params }: Props) {
  const { id: sessionId } = use(params)
  const { report, loading, error } = useReport(sessionId)

  function handleCopyLink() {
    navigator.clipboard.writeText(window.location.href)
  }

  function handleDownloadJson() {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `report-${sessionId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-zinc-400 text-sm animate-pulse">리포트 불러오는 중...</p>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-red-400 text-sm">{error ?? "리포트를 찾을 수 없습니다."}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <motion.div initial="hidden" animate="show" variants={fadeDown}>
        <AppHeader
          reportTitle="시뮬레이션 리포트"
          reportCreatedAt={formatDate(report.createdAt)}
          onCopyLink={handleCopyLink}
          onDownloadJson={handleDownloadJson}
        />
      </motion.div>

      <motion.main
        initial="hidden"
        animate="show"
        variants={staggerContainer(0.12, 0.2)}
        className="flex-1 max-w-3xl w-full mx-auto px-4 py-8 flex flex-col gap-5"
      >
        <motion.div variants={fadeUp}><TeamSection team={report.team} /></motion.div>
        <motion.div variants={fadeUp}><MetricsSection metrics={report.metrics} /></motion.div>
        <motion.div variants={fadeUp}><MeetingSummarySection data={report.meetingSummary} /></motion.div>
        <motion.div variants={fadeUp}><RecommendationSection recommendations={report.recommendations} /></motion.div>
      </motion.main>
    </div>
  )
}
