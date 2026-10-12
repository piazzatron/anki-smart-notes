import type { ButtonHTMLAttributes, ReactNode } from "react"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: "primary" | "quiet" | "danger" | "success"
}

// Flat fills only: variants differ by color, never by an outline.
const VARIANT_CLASSES = {
  primary: "bg-indigo text-white hover:bg-indigo/90",
  success: "bg-mint text-emerald-950 hover:bg-mint/90",
  quiet: "bg-white/[0.07] text-zinc-200 hover:bg-white/[0.11]",
  danger: "bg-red-300/[0.12] text-danger hover:bg-red-300/[0.18]",
}

export const Button = ({
  children,
  className = "",
  variant = "quiet",
  ...props
}: ButtonProps) => (
  <button
    className={`inline-flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-45 ${VARIANT_CLASSES[variant]} ${className}`}
    {...props}
  >
    {children}
  </button>
)
