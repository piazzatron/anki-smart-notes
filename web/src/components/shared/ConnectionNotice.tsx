import { LoaderCircle, WifiOff } from "lucide-react"
import { useTranslation } from "react-i18next"

import type { Connection } from "@/store/appStore"

interface ConnectionNoticeProps {
  connection: Connection
}

export const ConnectionNotice = ({ connection }: ConnectionNoticeProps) => {
  const { t } = useTranslation()
  if (connection === "connected") return null

  return (
    <div className="flex items-center gap-2 bg-caution/[0.08] px-6 py-2 text-[13px] text-caution-soft">
      {connection === "connecting" ? (
        <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
      ) : (
        <WifiOff aria-hidden className="size-3.5" />
      )}
      {connection === "connecting"
        ? t("common.connection.connecting")
        : t("common.connection.reconnecting")}
    </div>
  )
}
