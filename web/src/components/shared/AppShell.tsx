import type { ReactNode } from "react"

import { ConnectionNotice } from "./ConnectionNotice"
import { Sidebar } from "./Sidebar"

import type { Connection } from "@/store/appStore"
import type { ScreenId } from "@/lib/boot"
import type { AccountState } from "@/types/api"

interface AppShellProps {
  account: AccountState
  activeScreen: ScreenId
  appVersion: string | null
  connection: Connection
  children: ReactNode
  onNavigate: (screen: ScreenId) => void
}

export const AppShell = ({
  account,
  activeScreen,
  appVersion,
  connection,
  children,
  onNavigate,
}: AppShellProps) => {
  // Signed-out users can still sign in from Account and Usage, so only the
  // other screens are blocked.
  const isBlocked =
    account.status === "UNAUTHENTICATED" && activeScreen !== "subscription"

  return (
    <div className="flex h-full min-h-0 w-full bg-sidebar text-ink">
      <Sidebar
        account={account}
        activeScreen={activeScreen}
        appVersion={appVersion}
        onNavigate={onNavigate}
      />
      <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden border-s border-hairline bg-canvas">
        <div
          className="flex min-h-0 flex-1 flex-col"
          inert={isBlocked ? true : undefined}
        >
          <ConnectionNotice connection={connection} />
          {children}
        </div>
        {isBlocked && (
          <div
            aria-hidden
            className="absolute inset-0 z-20 cursor-default bg-black/45"
          />
        )}
      </main>
    </div>
  )
}
