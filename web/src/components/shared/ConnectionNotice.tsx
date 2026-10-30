import { useState } from "react"
import { LoaderCircle, WifiOff } from "lucide-react"
import { useTranslation } from "react-i18next"

import { Button } from "@/components/ui/Button"
import { refreshAccount } from "@/services/commands"
import { useAppStore, type Connection } from "@/store/appStore"
import type { AppState } from "@/types/api"

interface ConnectionNoticeProps {
  connection: Connection
}

export const ConnectionNotice = ({ connection }: ConnectionNoticeProps) => {
  const { t } = useTranslation()
  const state = useAppStore((store) => store.state)
  // A retry is in flight until the plugin pushes the next state, which it
  // does after every attempt.
  const [retriedFrom, setRetriedFrom] = useState<AppState | null>(null)

  const isServerUnreachable =
    connection === "connected" && state?.serverUnreachable === true
  if (connection === "connected" && !isServerUnreachable) return null
  const isRetrying = retriedFrom === state

  return (
    <div
      className="flex items-center gap-2 bg-caution/[0.08] px-6 py-2 text-[13px] text-caution-soft"
      role="status"
    >
      {connection === "connecting" ? (
        <LoaderCircle aria-hidden className="size-3.5 shrink-0 animate-spin" />
      ) : (
        <WifiOff aria-hidden className="size-3.5 shrink-0" />
      )}
      <span className="min-w-0 flex-1">
        {connection === "connecting"
          ? t("common.connection.connecting")
          : connection === "reconnecting"
            ? t("common.connection.reconnecting")
            : t("common.connection.serverUnreachable")}
      </span>
      {isServerUnreachable && (
        // aria-disabled rather than disabled, so keyboard focus stays on the
        // button through a retry.
        <Button
          aria-busy={isRetrying}
          aria-disabled={isRetrying}
          className="shrink-0 px-3 py-[5px] text-[12.5px] aria-disabled:cursor-default aria-disabled:opacity-45"
          onClick={() => {
            if (isRetrying) return
            setRetriedFrom(state)
            void refreshAccount()
          }}
        >
          {isRetrying && (
            <LoaderCircle aria-hidden className="size-3 animate-spin" />
          )}
          {t("common.connection.tryAgain")}
        </Button>
      )}
    </div>
  )
}
