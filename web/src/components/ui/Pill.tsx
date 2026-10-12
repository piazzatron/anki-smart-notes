import type { ReactNode } from "react"

interface PillProps {
  children: ReactNode
  className?: string
  tone?: "neutral" | "indigo" | "amber" | "warning"
}

const TONE_CLASSES = {
  neutral: "bg-white/[0.08] text-zinc-300",
  indigo: "bg-indigo/22 text-indigo-soft",
  amber: "bg-amber/[0.14] text-amber",
  // Solid, for costs people must not miss.
  warning: "bg-amber text-zinc-950",
}

/** The small rounded label shared across the app for metadata: decks, costs,
 *  providers, usage, and what a test ran with. Fill only — pills never get a border. */
export const Pill = ({
  children,
  className = "",
  tone = "neutral",
}: PillProps) => (
  <span
    className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-[3px] text-[10.5px] leading-4 font-semibold whitespace-nowrap ${TONE_CLASSES[tone]} ${className}`}
  >
    {children}
  </span>
)
