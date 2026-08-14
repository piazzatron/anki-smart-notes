import {
  CreditCard,
  Image,
  Layers3,
  LifeBuoy,
  MessageSquareText,
  SlidersHorizontal,
  Volume2,
} from "lucide-react"
import type { ComponentType } from "react"

import { DiscordMark } from "./DiscordMark"
import { FeedbackDialog } from "./FeedbackDialog"
import { PlanCard } from "./PlanCard"

import type { ScreenId } from "@/lib/boot"
import { DISCORD_URL } from "@/lib/helpChannels"
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

const PRIMARY_ITEMS: NavItem[] = [
  { id: "fields", label: "Smart Fields", icon: Layers3 },
  { id: "defaults-text", label: "Text", icon: MessageSquareText },
  { id: "defaults-voice", label: "Voice ", icon: Volume2 },
  { id: "defaults-images", label: "Image", icon: Image },
  { id: "settings", label: "Advanced Settings", icon: SlidersHorizontal },
]

const SECONDARY_ITEMS: NavItem[] = [
  { id: "support", label: "Support", icon: LifeBuoy },
  { id: "subscription", label: "Account and Usage", icon: CreditCard },
]

export const Sidebar = ({
  account,
  activeScreen,
  appVersion,
  onNavigate,
}: SidebarProps) => {
  return (
    <aside className="flex min-h-0 w-52 shrink-0 flex-col bg-sidebar px-2.5 pt-4 pb-0 max-[760px]:w-44">
      <div className="mb-3 px-2 text-[16px] font-bold text-zinc-100">
        Smart Notes
      </div>
      <nav
        aria-label="Smart Notes sections"
        className="min-h-0 flex-1 overflow-y-auto pb-2"
      >
        <div className="space-y-0.5">
          {PRIMARY_ITEMS.map((item) => (
            <NavButton
              activeScreen={activeScreen}
              item={item}
              key={item.id}
              onNavigate={onNavigate}
            />
          ))}
        </div>

        <div className="mx-2 my-2 border-t border-white/[0.06]" />
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
            className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-white/[0.06] py-[7px] text-[11px] font-semibold text-zinc-400 transition hover:bg-white/10 hover:text-zinc-200"
            href={DISCORD_URL}
            rel="noreferrer"
            target="_blank"
          >
            <DiscordMark className="text-zinc-300" size={13} />
            Discord
          </a>
          <FeedbackDialog>
            <button
              className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-white/[0.06] py-[7px] text-[11px] font-semibold text-zinc-400 transition hover:bg-white/10 hover:text-zinc-200"
              type="button"
            >
              <span aria-hidden className="text-xs leading-none">
                💡
              </span>
              Feedback
            </button>
          </FeedbackDialog>
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
      className={`flex w-full items-center gap-2.5 rounded-lg px-2 py-1 text-left text-[14px] font-medium transition-[background-color,color,opacity] duration-150 ease-out ${
        isActive
          ? "bg-white/[0.075] text-white opacity-100"
          : "text-zinc-400 opacity-80 hover:bg-white/[0.055] hover:text-zinc-100 hover:opacity-100"
      }`}
      onClick={() => onNavigate(item.id)}
    >
      <Icon aria-hidden className="size-[17px] shrink-0 opacity-85" />
      <span className="truncate">{item.label}</span>
    </button>
  )
}
