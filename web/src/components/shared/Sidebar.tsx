import { DiscordMark } from "./DiscordMark"
import { FeedbackDialog } from "./FeedbackDialog"
import { PlanCard } from "./PlanCard"
import { useTranslation } from "react-i18next"

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
  labelKey: string
  emoji: string
}

// Text and Image reuse the app's field-type emoji (💬 / 🎨). Smart Fields uses ✨
// to echo the "Smart Fields" page title; Voice uses the louder 🔊, which reads
// better at nav size than the field rows' quieter 🔈.
const PRIMARY_ITEMS: NavItem[] = [
  { id: "fields", labelKey: "smartFields", emoji: "✨" },
  { id: "defaults-text", labelKey: "text", emoji: "💬" },
  { id: "defaults-voice", labelKey: "voice", emoji: "🔊" },
  { id: "defaults-images", labelKey: "image", emoji: "🎨" },
  { id: "settings", labelKey: "settings", emoji: "⚙️" },
]

const SECONDARY_ITEMS: NavItem[] = [
  { id: "support", labelKey: "support", emoji: "🛟" },
  { id: "subscription", labelKey: "subscription", emoji: "💳" },
]

export const Sidebar = ({
  account,
  activeScreen,
  appVersion,
  onNavigate,
}: SidebarProps) => {
  const { t } = useTranslation()

  return (
    <aside className="flex min-h-0 w-[236px] shrink-0 flex-col bg-sidebar px-3 pt-4 pb-0 max-[760px]:w-48">
      <div className="mb-3.5 px-[7px] text-[18px] font-bold text-zinc-100">
        {t("common.productName")}
      </div>
      <nav
        aria-label={t("sidebar.sections")}
        className="min-h-0 flex-1 overflow-y-auto pb-2"
      >
        <div className="space-y-px">
          {PRIMARY_ITEMS.map((item) => (
            <NavButton
              activeScreen={activeScreen}
              item={item}
              key={item.id}
              onNavigate={onNavigate}
            />
          ))}
        </div>

        <div className="mx-3 mt-[10px] mb-[8px] border-t border-white/[0.06]" />
        <div className="space-y-px">
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
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-white/[0.06] py-2 text-[12px] font-semibold text-zinc-400 transition hover:bg-white/10 hover:text-zinc-200"
            href={DISCORD_URL}
            rel="noreferrer"
            target="_blank"
          >
            <DiscordMark className="text-zinc-300" size={14} />
            {t("sidebar.discord")}
          </a>
          <FeedbackDialog>
            <button
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-white/[0.06] py-2 text-[12px] font-semibold text-zinc-400 transition hover:bg-white/10 hover:text-zinc-200"
              type="button"
            >
              <span aria-hidden className="text-sm leading-none">
                💡
              </span>
              {t("sidebar.feedback")}
            </button>
          </FeedbackDialog>
        </div>

        {appVersion !== null && (
          <button
            className="block w-full pb-2 text-center font-mono text-[11px] text-zinc-600 hover:text-zinc-400"
            onClick={() => onNavigate("support")}
          >
            {t("sidebar.version", { version: appVersion })}
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
  const { t } = useTranslation()
  const isActive = item.id === activeScreen

  return (
    <button
      aria-current={isActive ? "page" : undefined}
      className={`flex w-full items-center gap-[10px] rounded-lg px-[10px] py-[5px] text-start text-[14px] font-medium transition-[background-color,color,opacity] duration-150 ease-out ${
        isActive
          ? "bg-[#7882ff]/[0.14] text-indigo-soft opacity-100"
          : "text-zinc-400 opacity-80 hover:bg-white/[0.055] hover:text-zinc-100 hover:opacity-100"
      }`}
      onClick={() => onNavigate(item.id)}
    >
      <span
        aria-hidden
        className="flex size-[18px] shrink-0 -translate-y-[0.5px] items-center justify-center text-[17px] leading-none"
      >
        {item.emoji}
      </span>
      <span className="truncate">{t(`sidebar.nav.${item.labelKey}`)}</span>
    </button>
  )
}
