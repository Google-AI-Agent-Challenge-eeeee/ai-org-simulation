"use client"

import { use } from "react"
import { motion } from "framer-motion"
import { ArrowLeft, FileText, Layers, Users } from "lucide-react"
import { useRouter } from "next/navigation"
import { ProgressStepper } from "@/components/layout/ProgressStepper"
import { FeaturePriorityBoard } from "@/components/requirements/FeaturePriorityBoard"
import { MilestoneTimeline } from "@/components/requirements/MilestoneTimeline"
import { PmReviewPanel } from "@/components/requirements/PmReviewPanel"
import { SectionHeader } from "@/components/ui/section-header"
import { useRequirementsReview } from "@/hooks/useRequirementsReview"
import { fadeUp, staggerContainer } from "@/lib/motion"

interface Props {
  params: Promise<{ id: string }>
}

export default function RequirementsPage({ params }: Props) {
  const { id: sessionId } = use(params)
  const router = useRouter()

  const {
    requirements,
    feedback, setFeedback,
    loading,
    actionLoading,
    error,
    pmPersona,
    handleAccept,
    handleRevise,
  } = useRequirementsReview(sessionId)
  const projectName = requirements?.project_name.replace(/^PDF 첨부:\s*/, "")

  return (
    <div className="min-h-screen flex flex-col bg-[#0f0f13]">
      {/* 헤더 */}
      <header
        className="flex items-center justify-between px-8 py-4 border-b border-white/5 bg-[#0f0f13]/80 backdrop-blur-md"
      >
        <button
          type="button"
          onClick={() => router.back()}
          className="flex cursor-pointer items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          뒤로
        </button>
        <div />
      </header>

      {/* 스텝퍼 */}
      <div className="pt-6 pb-3 px-4">
        <ProgressStepper currentStep="requirements" />
      </div>

      {/* 오류 */}
      {error && (
        <div className="mx-4 mt-4 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* 로딩 */}
      {loading && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <p className="text-sm text-zinc-400 animate-pulse">요구사항 분석 중...</p>
        </div>
      )}

      {/* 본문 */}
      {!loading && requirements && (
        <motion.div
          initial="hidden" animate="show"
          variants={staggerContainer(0.08, 0.1)}
          className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6 max-w-6xl mx-auto w-full px-4 pt-6"
        >
          {/* ─── Left ─── */}
          <motion.div variants={fadeUp} className="flex flex-col gap-5">
            {/* 프로젝트 개요 */}
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
              <div className="flex items-start justify-between gap-3 mb-2">
                <h2 className="text-lg font-bold text-zinc-100">{projectName}</h2>
                <FileText className="w-4 h-4 text-zinc-500 shrink-0 mt-1" />
              </div>
              <p className="text-sm text-zinc-400 leading-relaxed mb-3">{requirements.project_summary}</p>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs bg-zinc-800 border border-zinc-700 text-zinc-300 px-2.5 py-1 rounded-full">
                  📅 {requirements.timeline_days}일
                </span>
                <span className="text-xs bg-zinc-800 border border-zinc-700 text-zinc-300 px-2.5 py-1 rounded-full">
                  👥 {requirements.required_roles.length} roles
                </span>
                <span className="text-xs bg-zinc-800 border border-zinc-700 text-zinc-300 px-2.5 py-1 rounded-full">
                  ⚙️ {requirements.features.length} features
                </span>
              </div>
            </div>

            {/* 역할 & 스킬 */}
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
              <SectionHeader icon={Users} title="필수 역할 & 스킬" />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 mb-2">역할</p>
                  <div className="flex flex-wrap gap-1.5">
                    {requirements.required_roles.map((r) => (
                      <span key={r} className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 mb-2">스킬</p>
                  <div className="flex flex-wrap gap-1.5">
                    {requirements.required_skills.map((s) => (
                      <span key={s} className="text-xs bg-zinc-800 border border-zinc-700 text-zinc-300 px-2.5 py-1 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 기능 요구사항 */}
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
              <div className="flex items-center justify-between mb-4">
                <SectionHeader icon={Layers} title="기능 요구사항 분석" className="mb-0" />
                <span className="text-xs bg-zinc-800 border border-zinc-700 text-zinc-400 px-2.5 py-1 rounded-full">
                  우선순위 분류
                </span>
              </div>
              <FeaturePriorityBoard features={requirements.features} />
            </div>

            {/* 일정 & 마일스톤 */}
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-5">
              <SectionHeader icon={FileText} title="일정 & 마일스톤" />
              <MilestoneTimeline milestones={requirements.milestones} />
            </div>
          </motion.div>

          {/* ─── Right (sticky review panel) ─── */}
          <motion.div variants={fadeUp}>
            <PmReviewPanel
              confidence={requirements.confidence}
              pmPersona={pmPersona}
              feedback={feedback}
              onFeedbackChange={setFeedback}
              onAccept={handleAccept}
              onRevise={handleRevise}
              isLoading={actionLoading}
            />
          </motion.div>
        </motion.div>
      )}

    </div>
  )
}
