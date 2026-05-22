/**
 * Framer Motion 재사용 variants
 * 원칙: 빠르고(0.45s 이하) 자연스럽게(easeOut), 과하지 않게(y 16px 이하)
 */

export const ease: [number, number, number, number] = [0.25, 0.46, 0.45, 0.94]

/** 아래서 위로 페이드인 / 위로 페이드아웃 */
export const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show:   { opacity: 1, y: 0,  transition: { duration: 0.45, ease } },
}

/** 위에서 아래로 페이드인 (헤더 등) */
export const fadeDown = {
  hidden: { opacity: 0, y: -12 },
  show:   { opacity: 1, y: 0,  transition: { duration: 0.4, ease } },
}

/** 단순 페이드인 */
export const fadeIn = {
  hidden: { opacity: 0 },
  show:   { opacity: 1, transition: { duration: 0.5, ease } },
}

/** 살짝 스케일업 + 페이드인 (뱃지, 카드 등) */
export const popIn = {
  hidden: { opacity: 0, scale: 0.96 },
  show:   { opacity: 1, scale: 1, transition: { duration: 0.4, ease } },
}

/** 자식 요소 순차 등장 컨테이너 */
export function staggerContainer(stagger = 0.1, delayStart = 0) {
  return {
    hidden: {},
    show: {
      transition: {
        staggerChildren: stagger,
        delayChildren: delayStart,
      },
    },
  }
}

/** whileInView 공통 props — once: false 로 스크롤 재진입 시 재생 */
export const inView = {
  initial: "hidden",
  whileInView: "show",
  viewport: { once: false, amount: 0.15 },
} as const
