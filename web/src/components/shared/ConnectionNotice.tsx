import { LoaderCircle, WifiOff } from "lucide-react"

import type { Connection } from "@/store/appStore"

interface ConnectionNoticeProps {
  connection: Connection
}

export const ConnectionNotice = ({ connection }: ConnectionNoticeProps) => {
  if (connection === "connected") return null

  return (
    <div className="flex items-center gap-2 border-b border-amber/15 bg-amber/[0.06] px-6 py-2 text-[11px] text-amber">
      {connection === "connecting" ? (
        <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
      ) : (
        <WifiOff aria-hidden className="size-3.5" />
      )}
      {connection === "connecting"
        ? "Connecting to Anki…"
        : "Reconnecting to Anki…"}
    </div>
  )
}
