"use client"

import { use } from "react"
import { motion } from "framer-motion"
import { AppHeader } from "@/components/layout/AppHeader"
import { TeamSection } from "@/components/report/TeamSection"
import { MetricsSection } from "@/components/report/MetricsSection"
import { MeetingSummarySection } from "@/components/report/MeetingSummarySection"
import { RecommendationSection } from "@/components/report/RecommendationSection"
import { RequirementsSummarySection } from "@/components/report/RequirementsSummarySection"
import { PhaseSimulationSection } from "@/components/report/PhaseSimulationSection"
import { RoleplayOutputSection } from "@/components/report/RoleplayOutputSection"
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

  function handleDownloadPdf() {
    if (!report) return
    const previousTitle = document.title
    document.title = `report-${sessionId}`
    window.print()
    document.title = previousTitle
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f0f13]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <p className="text-zinc-400 text-sm animate-pulse">리포트 불러오는 중...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f0f13]">
        <p className="text-red-400 text-sm">{error ?? "리포트를 찾을 수 없습니다."}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#0f0f13] print-surface">
      <motion.div initial="hidden" animate="show" variants={fadeDown}>
        <AppHeader
          reportTitle="시뮬레이션 리포트"
          reportCreatedAt={formatDate(report.createdAt)}
          reportId={`SIM-${sessionId.slice(-6).toUpperCase()}`}
          projectName={report.selectedTeam?.teamName ?? "Project Alpha"}
          onCopyLink={handleCopyLink}
          onDownloadPdf={handleDownloadPdf}
        />
      </motion.div>

      <motion.main
        initial="hidden"
        animate="show"
        variants={staggerContainer(0.1, 0.15)}
        className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 flex flex-col gap-5"
      >
        {/* 요구사항 분석 요약 */}
        {report.requirementsSummary && (
          <motion.div variants={fadeUp}>
            <RequirementsSummarySection data={report.requirementsSummary} />
          </motion.div>
        )}

        {/* 수치 평가 */}
        <motion.div variants={fadeUp}>
          <MetricsSection metrics={report.metrics} />
        </motion.div>

        {/* 구성 팀 */}
        <motion.div variants={fadeUp}>
          <TeamSection
            team={report.team}
            pmPersona={report.pmPersona}
            selectedTeam={report.selectedTeam}
          />
        </motion.div>

        {/* 5단계 시뮬레이션 요약 */}
        {report.phaseSummaries && report.phaseSummaries.length > 0 && (
          <motion.div variants={fadeUp}>
            <PhaseSimulationSection
              phaseSummaries={report.phaseSummaries}
              footerNote="PhaseLogCollector → 리포트 생성 완료"
            />
          </motion.div>
        )}

        {/* 권고 사항 */}
        <motion.div variants={fadeUp}>
          <RecommendationSection recommendations={report.recommendations} />
        </motion.div>

        {/* 킥오프 회의 요약 */}
        <motion.div variants={fadeUp}>
          <MeetingSummarySection data={report.meetingSummary} />
        </motion.div>
        <motion.div variants={fadeUp}>
          <RoleplayOutputSection
            reportSummary={report.reportSummary}
            scoreBreakdown={report.scoreBreakdown}
            topRisks={report.topRisks}
            mustFixBeforeStart={report.mustFixBeforeStart}
            evidenceSummary={report.evidenceSummary}
            phaseDetails={report.phaseDetails}
          />
        </motion.div>
      </motion.main>
    </div>
  )
}
