"use client"

import { motion } from "framer-motion"

const ease: [number, number, number, number] = [0.25, 0.46, 0.45, 0.94]

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35, ease }}
    >
      {children}
    </motion.div>
  )
}
