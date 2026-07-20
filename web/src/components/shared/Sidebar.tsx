import {
  CreditCard,
  Image,
  Layers3,
  LifeBuoy,
  MessageSquare,
  MessageSquareText,
  MessagesSquare,
  Settings,
  SlidersHorizontal,
  Volume2,
} from "lucide-react"
import type { ComponentType } from "react"

import { PlanCard } from "./PlanCard"

import type { ScreenId } from "@/lib/boot"

import type { AccountState } from "./planPresentation"

interface SidebarProps {
  account: AccountState
  activeScreen: ScreenId
  onNavigate: (screen: ScreenId) => void
}

interface NavItem {
  id: ScreenId
  label: string
  icon: ComponentType<{ className?: string; "aria-hidden"?: boolean }>
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Home",
    items: [{ id: "fields", label: "Smart Fields", icon: Layers3 }],
  },
  {
    label: "Defaults",
    items: [
      { id: "defaults-text", label: "Text", icon: MessageSquareText },
      { id: "defaults-images", label: "Images", icon: Image },
      { id: "defaults-voice", label: "Voice", icon: Volume2 },
    ],
  },
  {
    label: "Settings",
    items: [
      { id: "generation", label: "Generation", icon: SlidersHorizontal },
      { id: "advanced", label: "Advanced", icon: Settings },
    ],
  },
  {
    label: "Account",
    items: [
      { id: "subscription", label: "Subscription", icon: CreditCard },
      { id: "support", label: "Support & Bugs", icon: LifeBuoy },
    ],
  },
]

export const Sidebar = ({
  account,
  activeScreen,
  onNavigate,
}: SidebarProps) => (
  <aside className="flex min-h-0 w-52 shrink-0 flex-col border-r border-white/[0.065] bg-sidebar px-2.5 py-3.5 max-[760px]:w-44">
    <nav
      aria-label="Smart Notes sections"
      className="min-h-0 flex-1 overflow-y-auto"
    >
      {NAV_GROUPS.map((group) => (
        <section className="mb-3.5" key={group.label}>
          <h2 className="mb-1 px-2 text-[9px] font-semibold tracking-[0.12em] text-ink-faint uppercase">
            {group.label}
          </h2>
          <div className="space-y-0.5">
            {group.items.map((item) => {
              const Icon = item.icon
              const isActive = item.id === activeScreen

              return (
                <button
                  aria-current={isActive ? "page" : undefined}
                  className={`flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-[12.5px] font-medium transition ${
                    isActive
                      ? "bg-indigo/14 text-indigo-soft"
                      : "text-zinc-400 hover:bg-white/[0.045] hover:text-zinc-100"
                  }`}
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                >
                  <Icon
                    aria-hidden
                    className="size-[17px] shrink-0 opacity-85"
                  />
                  <span className="truncate">{item.label}</span>
                </button>
              )
            })}
          </div>
        </section>
      ))}
    </nav>

    <div className="mt-2 space-y-2.5">
      <PlanCard
        account={account}
        onOpenSubscription={() => onNavigate("subscription")}
      />
      <div className="grid grid-cols-2 gap-1.5">
        <a
          className="inline-flex items-center justify-center gap-1.5 rounded-md border border-white/[0.07] px-2 py-1.5 text-[10px] text-ink-faint transition hover:border-white/12 hover:text-zinc-300"
          href="https://discord.gg/kxGaWpkTGr"
          rel="noreferrer"
          target="_blank"
        >
          <MessagesSquare aria-hidden className="size-3" />
          Discord
        </a>
        <button
          className="inline-flex items-center justify-center gap-1.5 rounded-md border border-white/[0.07] px-2 py-1.5 text-[10px] text-ink-faint transition hover:border-white/12 hover:text-zinc-300"
          onClick={() => onNavigate("support")}
        >
          <MessageSquare aria-hidden className="size-3" />
          Feedback
        </button>
      </div>
      <p className="text-center text-[9px] tracking-wide text-zinc-700 uppercase">
        Beta UI
      </p>
    </div>
  </aside>
)
