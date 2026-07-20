import type { ReactNode } from "react"

import { ConnectionNotice } from "./ConnectionNotice"
import { Sidebar } from "./Sidebar"

import type { Connection } from "@/store/appStore"
import type { ScreenId } from "@/lib/boot"

import type { AccountState } from "./planPresentation"

interface AppShellProps {
  account: AccountState
  activeScreen: ScreenId
  connection: Connection
  children: ReactNode
  onNavigate: (screen: ScreenId) => void
}

export const AppShell = ({
  account,
  activeScreen,
  connection,
  children,
  onNavigate,
}: AppShellProps) => (
  <div className="flex h-full min-h-0 w-full bg-canvas text-ink">
    <Sidebar
      account={account}
      activeScreen={activeScreen}
      onNavigate={onNavigate}
    />
    <main className="flex min-w-0 flex-1 flex-col bg-canvas">
      <ConnectionNotice connection={connection} />
      {children}
    </main>
  </div>
)
