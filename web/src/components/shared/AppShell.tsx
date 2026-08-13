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
}: AppShellProps) => (
  <div className="flex h-full min-h-0 w-full bg-sidebar text-ink">
    <Sidebar
      account={account}
      activeScreen={activeScreen}
      appVersion={appVersion}
      onNavigate={onNavigate}
    />
    <main className="m-2 ml-0 flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl bg-canvas">
      <ConnectionNotice connection={connection} />
      {children}
    </main>
  </div>
)
