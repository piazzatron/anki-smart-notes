import type { ButtonHTMLAttributes, ReactNode } from "react"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: "primary" | "quiet" | "danger"
}

const VARIANT_CLASSES = {
  primary:
    "border-indigo/45 bg-indigo/14 text-indigo-soft hover:border-indigo/65 hover:bg-indigo/20",
  quiet:
    "border-white/10 bg-white/[0.035] text-zinc-300 hover:border-white/16 hover:bg-white/[0.065]",
  danger:
    "border-red-300/15 bg-red-300/[0.06] text-danger hover:border-red-300/25 hover:bg-red-300/10",
}

export const Button = ({
  children,
  className = "",
  variant = "quiet",
  ...props
}: ButtonProps) => (
  <button
    className={`inline-flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-45 ${VARIANT_CLASSES[variant]} ${className}`}
    {...props}
  >
    {children}
  </button>
)
