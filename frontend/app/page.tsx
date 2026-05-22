"use client"

import Link from "next/link"
import Image from "next/image"
import { motion } from "framer-motion"
import {
  Cpu, ArrowRight, FileText, Zap, BarChart3,
  ChevronRight, Users, TrendingUp, Shield,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { fadeUp, fadeDown, fadeIn, popIn, staggerContainer, inView } from "@/lib/motion"

/* ─── Navbar ─────────────────────────────── */
function Navbar() {
  return (
    <motion.nav
      initial="hidden" animate="show" variants={fadeDown}
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 border-b border-white/5 bg-[#0f0f13]/80 backdrop-blur-md"
    >
      <Link href="/" className="flex items-center gap-2">
        <Cpu className="w-5 h-5 text-indigo-400" />
        <span className="text-sm font-bold text-zinc-100 tracking-tight">
          Synthetic<span className="text-indigo-400">Intelligence</span>
        </span>
      </Link>

      <div className="hidden md:flex items-center gap-6 text-xs text-zinc-400">
        <a href="#how-it-works" className="hover:text-zinc-200 transition-colors">플랫폼</a>
        <a href="#how-it-works" className="hover:text-zinc-200 transition-colors">시뮬레이션</a>
        <a href="#integrations" className="hover:text-zinc-200 transition-colors">방법론</a>
        <a href="#integrations" className="hover:text-zinc-200 transition-colors">기업 솔루션</a>
      </div>

      <div className="flex items-center gap-3">
        <span className="hidden sm:block text-xs text-zinc-400 cursor-pointer hover:text-zinc-200 transition-colors">
          Sign In
        </span>
        <Link href="/simulate">
          <Button size="sm" className="gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold">
            New Simulation
            <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>
    </motion.nav>
  )
}

/* ─── Dashboard Mockup ───────────────────── */
function DashboardMockup() {
  return (
    <motion.div
      variants={fadeUp}
      className="relative w-full max-w-4xl mx-auto mt-16"
    >
      <div className="absolute inset-0 -z-10 blur-3xl opacity-25 bg-indigo-600 rounded-full scale-75" />
      <div className="rounded-2xl border border-zinc-700/60 bg-zinc-900/80 shadow-2xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800 bg-zinc-950/60">
          <span className="w-3 h-3 rounded-full bg-red-500/70" />
          <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
          <span className="w-3 h-3 rounded-full bg-green-500/70" />
          <span className="ml-3 text-xs text-zinc-500">AI Org Simulation — 킥오프 회의 진행 중</span>
        </div>
        <div className="grid grid-cols-12 gap-0 h-[340px]">
          {/* 사이드바 */}
          <div className="col-span-2 border-r border-zinc-800 p-3 flex flex-col gap-3">
            {["PM","BE","DS","iOS","QA"].map((role, i) => (
              <div key={role} className="flex items-center gap-2">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white ${["bg-purple-600","bg-blue-600","bg-pink-600","bg-slate-600","bg-amber-600"][i]}`}>
                  {role[0]}
                </div>
                <span className="text-[10px] text-zinc-400">{role}</span>
              </div>
            ))}
          </div>
          {/* 채팅 */}
          <div className="col-span-7 p-4 flex flex-col gap-3 overflow-hidden">
            {[
              { role:"PM", color:"bg-purple-600", text:"이번 스프린트 핵심은 로그인 API 연동입니다." },
              { role:"BE", color:"bg-blue-600",   text:"인증 플로우부터 시작하겠습니다. DB 스키마는 내일 공유드릴게요." },
              { role:"DS", color:"bg-pink-600",   text:"다크모드 컬러 토큰 정의가 먼저 필요합니다." },
              { role:"iOS",color:"bg-slate-600",  text:"API 문서만 나오면 바로 연동 작업 시작합니다." },
              { role:"QA", color:"bg-amber-600",  text:"E2E 테스트 병행 여부를 결정해주세요." },
            ].map((msg, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className={`w-5 h-5 rounded-full flex-shrink-0 ${msg.color} flex items-center justify-center text-[8px] font-bold text-white mt-0.5`}>
                  {msg.role[0]}
                </div>
                <div className="bg-zinc-800/80 rounded-lg px-3 py-1.5 max-w-[85%]">
                  <p className="text-[10px] text-zinc-300">{msg.text}</p>
                </div>
              </div>
            ))}
            <div className="flex items-center gap-1 ml-7">
              {[0,150,300].map((d) => (
                <span key={d} className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: `${d}ms` }} />
              ))}
            </div>
          </div>
          {/* 메트릭 */}
          <div className="col-span-3 border-l border-zinc-800 p-3 flex flex-col gap-3">
            <p className="text-[10px] text-zinc-500 font-medium">실시간 분석</p>
            <div className="bg-zinc-800/50 rounded-lg p-2.5">
              <p className="text-[9px] text-zinc-500 mb-1">팀 핏 스코어</p>
              <div className="flex items-end gap-1">
                <span className="text-2xl font-bold text-emerald-400">87</span>
                <span className="text-[10px] text-zinc-500 mb-0.5">/100</span>
              </div>
              <div className="mt-1.5 h-1 rounded-full bg-zinc-700">
                <div className="h-full rounded-full bg-emerald-500" style={{ width:"87%" }} />
              </div>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-2.5">
              <p className="text-[9px] text-zinc-500 mb-1">리스크 인덱스</p>
              <div className="flex items-end gap-1">
                <span className="text-2xl font-bold text-amber-400">23</span>
                <span className="text-[10px] text-zinc-500 mb-0.5">Low</span>
              </div>
              <div className="mt-1.5 flex gap-0.5 h-1.5">
                <div className="flex-[7] rounded-l-full bg-emerald-500" />
                <div className="flex-[2] bg-amber-500" />
                <div className="flex-[1] rounded-r-full bg-red-500" />
              </div>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-2.5">
              <p className="text-[9px] text-zinc-500 mb-1">예상 완성도</p>
              <div className="flex items-end gap-1">
                <span className="text-2xl font-bold text-indigo-400">91</span>
                <span className="text-[10px] text-zinc-500 mb-0.5">%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="mx-auto mt-0 h-4 w-1/3 bg-zinc-800/60 rounded-b-xl" />
      <div className="mx-auto h-2 w-1/4 bg-zinc-800/40 rounded-b-xl" />
    </motion.div>
  )
}

/* ─── How It Works ───────────────────────── */
function HowItWorksSection() {
  const steps = [
    { icon: FileText, step:"01", title:"PRD 입력",      desc:"제품 요구사항 문서 또는 기획서를 텍스트로 붙여넣거나 파일로 업로드하세요.",                           color:"text-indigo-400", bg:"bg-indigo-500/10 border-indigo-500/20" },
    { icon: Zap,      step:"02", title:"AI 시뮬레이션", desc:"AI 에이전트들이 최적 팀을 구성하고 가상 킥오프 회의를 실시간으로 진행합니다.",                       color:"text-purple-400", bg:"bg-purple-500/10 border-purple-500/20", active:true },
    { icon: BarChart3,step:"03", title:"결과 리포트",   desc:"팀 핏 스코어, 리스크 분석, 번아웃 예측, 병목 구간 권고안을 확인하세요.",                             color:"text-emerald-400",bg:"bg-emerald-500/10 border-emerald-500/20" },
  ]

  return (
    <section id="how-it-works" className="py-24 px-4">
      <div className="max-w-5xl mx-auto">
        {/* 제목 */}
        <motion.div {...inView} variants={staggerContainer(0.1)} className="text-center mb-14">
          <motion.p variants={fadeUp} className="text-xs text-indigo-400 font-semibold tracking-widest uppercase mb-3">How It Works</motion.p>
          <motion.h2 variants={fadeUp} className="text-3xl font-bold text-zinc-100">3단계로 끝나는 팀 최적화</motion.h2>
          <motion.p variants={fadeUp} className="mt-3 text-sm text-zinc-500">복잡한 조직 설계를 AI가 대신합니다</motion.p>
        </motion.div>

        {/* 카드 */}
        <motion.div
          {...inView}
          variants={staggerContainer(0.12, 0.05)}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 relative"
        >
          <div className="hidden md:block absolute top-12 left-1/3 right-1/3 h-px bg-gradient-to-r from-indigo-500/30 via-purple-500/30 to-emerald-500/30" />
          {steps.map((s) => (
            <motion.div
              key={s.step}
              variants={fadeUp}
              className={`relative rounded-2xl border p-6 flex flex-col gap-4 transition-all ${s.bg} ${s.active ? "ring-1 ring-purple-500/40 shadow-lg shadow-purple-500/10" : ""}`}
            >
              {s.active && (
                <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full bg-purple-600 text-[10px] font-bold text-white">
                  진행 중
                </span>
              )}
              <div className={`w-11 h-11 rounded-xl border ${s.bg} flex items-center justify-center`}>
                <s.icon className={`w-5 h-5 ${s.color}`} />
              </div>
              <div>
                <p className={`text-xs font-bold tracking-widest ${s.color} mb-1`}>{s.step}</p>
                <h3 className="text-base font-bold text-zinc-100 mb-2">{s.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{s.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        <motion.div {...inView} variants={fadeUp} className="mt-12 text-center">
          <Link href="/simulate">
            <Button className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6">
              지금 시작하기
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  )
}

/* ─── Metrics Strip ──────────────────────── */
function MetricsStrip() {
  const stats = [
    { icon: Users,      value:"5+",   label:"AI 페르소나 역할" },
    { icon: TrendingUp, value:"87",   label:"평균 팀 핏 스코어" },
    { icon: Shield,     value:"Low",  label:"평균 리스크 수준" },
    { icon: Zap,        value:"~2분", label:"시뮬레이션 소요 시간" },
  ]

  return (
    <motion.div
      {...inView}
      variants={staggerContainer(0.1)}
      className="border-y border-zinc-800/80 bg-zinc-900/40 py-10"
    >
      <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 px-6">
        {stats.map((s) => (
          <motion.div key={s.label} variants={fadeUp} className="flex flex-col items-center gap-2 text-center">
            <s.icon className="w-5 h-5 text-indigo-400" />
            <span className="text-2xl font-bold text-zinc-100">{s.value}</span>
            <span className="text-xs text-zinc-500">{s.label}</span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

/* ─── Integrations ───────────────────────── */
const INTEGRATION_ITEMS = [
  { name:"Slack",           src:"/integrations/slack.png",           pos:"top-6 left-6"    },
  { name:"Google Calendar", src:"/integrations/google-calendar.png", pos:"top-6 right-6"   },
  { name:"GitHub",          src:"/integrations/github.png",          pos:"bottom-6 left-6" },
  { name:"Jira",            src:"/integrations/jira.png",            pos:"bottom-6 right-6"},
]

function IntegrationsSection() {
  return (
    <section id="integrations" className="py-24 px-4">
      <div className="max-w-5xl mx-auto">
        <motion.div
          {...inView}
          variants={fadeIn}
          className="rounded-2xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 overflow-hidden"
        >
          <div className="grid md:grid-cols-2 gap-0">
            {/* 텍스트 */}
            <motion.div
              {...inView}
              variants={staggerContainer(0.1, 0.1)}
              className="p-10 flex flex-col justify-center gap-5"
            >
              <motion.p variants={fadeUp} className="text-xs text-indigo-400 font-semibold tracking-widest uppercase">Integrations</motion.p>
              <motion.h2 variants={fadeUp} className="text-2xl font-bold text-zinc-100">
                실제 업무 도구와<br />연결된 AI 분석
              </motion.h2>
              <motion.p variants={fadeUp} className="text-sm text-zinc-400 leading-relaxed">
                GitHub, Slack, Jira, 캘린더 데이터를 기반으로 실제 팀원 역량과 업무 패턴을 분석합니다.
                더 정확한 팀 구성과 리스크 예측이 가능합니다.
              </motion.p>
              <motion.div variants={fadeUp} className="flex items-center gap-3 flex-wrap">
                {INTEGRATION_ITEMS.map((item) => (
                  <div key={item.name} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-800/70 border border-zinc-700/50">
                    <Image src={item.src} alt={item.name} width={16} height={16} className="rounded-sm object-cover" />
                    <span className="text-[11px] text-zinc-400">{item.name}</span>
                  </div>
                ))}
              </motion.div>
              <motion.div variants={fadeUp}>
                <Link href="/simulate">
                  <Button variant="outline" size="sm" className="gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800 w-fit">
                    시뮬레이션 시작
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </motion.div>
            </motion.div>

            {/* 시각화 */}
            <div className="relative flex items-center justify-center p-10 bg-zinc-950/40 min-h-[220px]">
              <motion.div
                {...inView}
                variants={popIn}
                className="relative w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center z-10 shadow-lg shadow-indigo-500/20"
              >
                <Cpu className="w-7 h-7 text-indigo-400" />
              </motion.div>

              <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                {[
                  { x1:"22%", y1:"22%", x2:"50%", y2:"50%" },
                  { x1:"78%", y1:"22%", x2:"50%", y2:"50%" },
                  { x1:"22%", y1:"78%", x2:"50%", y2:"50%" },
                  { x1:"78%", y1:"78%", x2:"50%", y2:"50%" },
                ].map((line, i) => (
                  <line key={i} x1={line.x1} y1={line.y1} x2={line.x2} y2={line.y2}
                    stroke="rgba(99,102,241,0.3)" strokeWidth="1" strokeDasharray="5 4" />
                ))}
              </svg>

              {INTEGRATION_ITEMS.map((item, i) => (
                <motion.div
                  key={item.name}
                  {...inView}
                  variants={{ hidden:{ opacity:0, scale:0.8 }, show:{ opacity:1, scale:1, transition:{ duration:0.4, delay: i * 0.08, ease:[0.25,0.46,0.45,0.94] as [number,number,number,number] } } }}
                  className="absolute w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-700/60 shadow-lg flex items-center justify-center overflow-hidden"
                  style={{
                    top:    item.pos.includes("top-6")    ? "1.5rem" : "auto",
                    bottom: item.pos.includes("bottom-6") ? "1.5rem" : "auto",
                    left:   item.pos.includes("left-6")   ? "1.5rem" : "auto",
                    right:  item.pos.includes("right-6")  ? "1.5rem" : "auto",
                  }}
                  title={item.name}
                >
                  <Image src={item.src} alt={item.name} width={56} height={56} className="w-full h-full object-cover rounded-2xl" />
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

/* ─── Footer ─────────────────────────────── */
function Footer() {
  return (
    <motion.footer
      {...inView}
      variants={fadeIn}
      className="border-t border-zinc-800/60 py-8 px-6"
    >
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-zinc-400">
            Synthetic<span className="text-indigo-400">Intelligence</span>
          </span>
        </div>
        <div className="flex items-center gap-5 text-[11px] text-zinc-600">
          {["Privacy Policy","Terms of Service","API Documentation","Support"].map((t) => (
            <span key={t} className="hover:text-zinc-400 cursor-pointer transition-colors">{t}</span>
          ))}
        </div>
        <p className="text-[11px] text-zinc-600">© 2026 SyntheticIntelligence. All rights reserved.</p>
      </div>
    </motion.footer>
  )
}

/* ─── Landing Page ───────────────────────── */
export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0f0f13]">
      <Navbar />

      {/* Hero */}
      <section className="flex flex-col items-center text-center pt-36 pb-8 px-4">
        <motion.div
          initial="hidden"
          animate="show"
          variants={staggerContainer(0.1, 0.1)}
          className="flex flex-col items-center"
        >
          {/* 뱃지 */}
          <motion.div variants={popIn} className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            AI Organization Design Engine v1.0
          </motion.div>

          {/* 타이틀 */}
          <motion.h1 variants={fadeUp} className="text-5xl md:text-6xl font-extrabold text-zinc-100 leading-tight tracking-tight max-w-3xl">
            AI로 최적의<br />
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              팀 조직을 설계하세요
            </span>
          </motion.h1>

          {/* 서브텍스트 */}
          <motion.p variants={fadeUp} className="mt-5 text-base text-zinc-400 max-w-xl leading-relaxed">
            PRD를 입력하면 AI 에이전트들이 최적 팀을 구성하고 가상 킥오프 회의를 진행합니다.
            리스크 예측부터 번아웃 경고까지, 의사결정을 데이터로 뒷받침합니다.
          </motion.p>

          {/* CTA */}
          <motion.div variants={fadeUp} className="mt-8 flex items-center gap-3">
            <Link href="/simulate">
              <Button size="lg" className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-7 py-5 text-base">
                바로 시작
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <a href="#how-it-works">
              <Button size="lg" variant="outline" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 px-7 py-5 text-base">
                사례로 보기
              </Button>
            </a>
          </motion.div>

          {/* 대시보드 목업 */}
          <DashboardMockup />
        </motion.div>
      </section>

      <MetricsStrip />
      <HowItWorksSection />
      <IntegrationsSection />
      <Footer />
    </div>
  )
}
