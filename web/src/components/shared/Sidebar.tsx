import {
  CreditCard,
  Image,
  Layers3,
  LifeBuoy,
  MessageSquare,
  MessageSquareText,
  MessagesSquare,
  SlidersHorizontal,
  Volume2,
} from "lucide-react"
import type { ComponentType } from "react"

import { FeedbackPopover } from "./FeedbackPopover"
import { PlanCard } from "./PlanCard"

import type { ScreenId } from "@/lib/boot"
import type { AccountState } from "@/types/api"

interface SidebarProps {
  account: AccountState
  activeScreen: ScreenId
  appVersion: string | null
  onNavigate: (screen: ScreenId) => void
}

interface NavItem {
  id: ScreenId
  label: string
  icon: ComponentType<{ className?: string; "aria-hidden"?: boolean }>
}

const SMART_FIELDS_ITEM: NavItem = {
  id: "fields",
  label: "Smart Fields",
  icon: Layers3,
}

const DEFAULT_ITEMS: NavItem[] = [
  { id: "defaults-text", label: "Text", icon: MessageSquareText },
  { id: "defaults-images", label: "Images", icon: Image },
  { id: "defaults-voice", label: "Voice", icon: Volume2 },
]

const SECONDARY_ITEMS: NavItem[] = [
  { id: "settings", label: "Settings", icon: SlidersHorizontal },
  { id: "subscription", label: "Subscription", icon: CreditCard },
  { id: "support", label: "Support & Bugs", icon: LifeBuoy },
]

export const Sidebar = ({
  account,
  activeScreen,
  appVersion,
  onNavigate,
}: SidebarProps) => {
  return (
    <aside className="flex min-h-0 w-52 shrink-0 flex-col border-r border-white/[0.065] bg-sidebar px-2.5 pt-4 pb-0 max-[760px]:w-44">
      <nav
        aria-label="Smart Notes sections"
        className="min-h-0 flex-1 overflow-y-auto pb-2"
      >
        <NavButton
          activeScreen={activeScreen}
          item={SMART_FIELDS_ITEM}
          onNavigate={onNavigate}
        />

        <h2 className="mt-4 mb-1 px-2 text-[10px] font-semibold tracking-[0.12em] text-zinc-500 uppercase">
          Defaults
        </h2>
        <div className="space-y-0.5">
          {DEFAULT_ITEMS.map((item) => (
            <NavButton
              activeScreen={activeScreen}
              item={item}
              key={item.id}
              onNavigate={onNavigate}
            />
          ))}
        </div>

        <div className="mx-2 my-2.5 border-t border-white/[0.06]" />
        <div className="space-y-0.5">
          {SECONDARY_ITEMS.map((item) => (
            <NavButton
              activeScreen={activeScreen}
              item={item}
              key={item.id}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      </nav>

      <div className="space-y-2.5 px-0 pb-0">
        <PlanCard
          account={account}
          onOpenSubscription={() => onNavigate("subscription")}
        />
        <div className="relative grid grid-cols-2 gap-1.5">
          <a
            className="inline-flex items-center justify-center gap-1.5 rounded-md border border-white/[0.07] px-2 py-1.5 text-[10px] text-ink-faint transition hover:border-white/12 hover:text-zinc-300"
            href="https://discord.gg/kxGaWpkTGr"
            rel="noreferrer"
            target="_blank"
          >
            <MessagesSquare aria-hidden className="size-3" />
            Discord
          </a>
          <FeedbackPopover onOpenSupport={() => onNavigate("support")}>
            <button className="inline-flex items-center justify-center gap-1.5 rounded-md border border-white/[0.07] px-2 py-1.5 text-[10px] text-ink-faint transition hover:border-white/12 hover:text-zinc-300">
              <MessageSquare aria-hidden className="size-3" />
              Feedback
            </button>
          </FeedbackPopover>
        </div>

        {appVersion !== null && (
          <button
            className="block w-full pb-2 text-center font-mono text-[10px] text-zinc-600 hover:text-zinc-400"
            onClick={() => onNavigate("support")}
          >
            Smart Notes v{appVersion}
          </button>
        )}
      </div>
    </aside>
  )
}

interface NavButtonProps {
  activeScreen: ScreenId
  item: NavItem
  onNavigate: (screen: ScreenId) => void
}

const NavButton = ({ activeScreen, item, onNavigate }: NavButtonProps) => {
  const Icon = item.icon
  const isActive = item.id === activeScreen

  return (
    <button
      aria-current={isActive ? "page" : undefined}
      className={`flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-[14px] font-medium transition ${
        isActive
          ? "bg-indigo/14 text-indigo-soft"
          : "text-zinc-300 hover:bg-white/[0.055] hover:text-zinc-100"
      }`}
      onClick={() => onNavigate(item.id)}
    >
      <Icon aria-hidden className="size-[17px] shrink-0 opacity-85" />
      <span className="truncate">{item.label}</span>
    </button>
  )
}
