import type { ReactNode } from "react"

import { ConnectionNotice } from "./ConnectionNotice"
import { Sidebar } from "./Sidebar"

import type { Connection } from "@/store/appStore"
import type { ScreenId } from "@/lib/boot"
import type { AccountState, Settings } from "@/types/api"

interface AppShellProps {
  account: AccountState
  activeScreen: ScreenId
  appVersion: string | null
  connection: Connection
  settings: Settings | null
  children: ReactNode
  onNavigate: (screen: ScreenId) => void
}

export const AppShell = ({
  account,
  activeScreen,
  appVersion,
  connection,
  settings,
  children,
  onNavigate,
}: AppShellProps) => {
  const isSignedOut = account.status === "UNAUTHENTICATED"

  return (
    <div className="flex h-full min-h-0 w-full bg-sidebar text-ink">
      <Sidebar
        account={account}
        activeScreen={activeScreen}
        appVersion={appVersion}
        settings={settings}
        onNavigate={onNavigate}
      />
      <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden border-s border-white/[0.04] bg-canvas">
        <div
          className="flex min-h-0 flex-1 flex-col"
          inert={isSignedOut ? true : undefined}
        >
          <ConnectionNotice connection={connection} />
          {children}
        </div>
        {isSignedOut && (
          <div
            aria-hidden
            className="absolute inset-0 z-20 cursor-default bg-black/45"
          />
        )}
      </main>
    </div>
  )
}
