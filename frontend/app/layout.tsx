import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "AI Org Simulation",
  description: "PRD와 PM 요구사항을 입력하면 최적의 팀을 시뮬레이션합니다.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko" className="h-full">
      <body className="min-h-full flex flex-col bg-[#0f0f13] text-zinc-100 antialiased">
        {children}
      </body>
    </html>
  )
}
