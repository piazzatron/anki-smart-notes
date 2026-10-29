import { DiscordMark } from "./DiscordMark"
import { FeedbackDialog } from "./FeedbackDialog"
import {
  CardIcon,
  ChatIcon,
  CogIcon,
  GalleryIcon,
  type IconProps,
  LifebuoyIcon,
  LightbulbIcon,
  SparklesIcon,
  VolumeIcon,
} from "./Icons"
import { PlanCard } from "./PlanCard"
import { resizeSidebar } from "./sidebarWidth"
import { useDirection } from "@radix-ui/react-direction"
import { type ComponentType, useRef, useState, type PointerEvent } from "react"
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

interface ResizeDrag {
  pointerStartX: number
  startWidth: number
}

interface NavItem {
  id: ScreenId
  labelKey: string
  icon: ComponentType<IconProps>
}

// Flat ink icons in the label's own color, instead of emoji, which render
// differently on every OS.
const PRIMARY_ITEMS: NavItem[] = [
  { id: "fields", labelKey: "smartFields", icon: SparklesIcon },
]

const DEFAULTS_ITEMS: NavItem[] = [
  { id: "defaults-text", labelKey: "text", icon: ChatIcon },
  { id: "defaults-voice", labelKey: "voice", icon: VolumeIcon },
  { id: "defaults-images", labelKey: "image", icon: GalleryIcon },
]

const SECONDARY_ITEMS: NavItem[] = [
  { id: "settings", labelKey: "settings", icon: CogIcon },
  { id: "support", labelKey: "support", icon: LifebuoyIcon },
  { id: "subscription", labelKey: "subscription", icon: CardIcon },
]

export const Sidebar = ({
  account,
  activeScreen,
  appVersion,
  onNavigate,
}: SidebarProps) => {
  const { t } = useTranslation()
  const direction = useDirection()
  const asideRef = useRef<HTMLElement>(null)
  const dragRef = useRef<ResizeDrag | null>(null)
  const [isResizing, setIsResizing] = useState(false)
  // Until the user drags, the sidebar keeps its responsive CSS width.
  const [width, setWidth] = useState<number | null>(null)

  const startResize = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0 || asideRef.current === null) return
    event.preventDefault()
    event.currentTarget.setPointerCapture(event.pointerId)
    dragRef.current = {
      pointerStartX: event.clientX,
      startWidth: asideRef.current.getBoundingClientRect().width,
    }
    setIsResizing(true)
  }

  const moveResize = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current
    if (drag === null) return
    setWidth(
      resizeSidebar(
        drag.startWidth,
        event.clientX - drag.pointerStartX,
        direction,
      ),
    )
  }

  const endResize = () => {
    dragRef.current = null
    setIsResizing(false)
  }

  return (
    <aside
      className="relative flex min-h-0 w-[236px] max-w-[40vw] shrink-0 flex-col bg-sidebar px-3 pt-4 pb-0 max-[760px]:w-48"
      ref={asideRef}
      style={width === null ? undefined : { width }}
    >
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

        {/* A group label like Linear's sidebar sections: sentence case, quieter than the items. */}
        <div className="mt-[13px] mb-1 px-[10px] text-[13px] leading-5 font-medium text-ink-muted">
          {t("sidebar.defaults")}
        </div>
        <div className="space-y-px">
          {DEFAULTS_ITEMS.map((item) => (
            <NavButton
              activeScreen={activeScreen}
              item={item}
              key={item.id}
              onNavigate={onNavigate}
            />
          ))}
        </div>

        <div className="mx-[10px] my-2 h-px bg-white/[0.08]" />
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
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-white/[0.06] py-2 text-[13px] font-semibold text-zinc-400 transition hover:bg-white/10 hover:text-zinc-200"
            href={DISCORD_URL}
            rel="noreferrer"
            target="_blank"
          >
            <DiscordMark className="text-zinc-300" size={14} />
            {t("sidebar.discord")}
          </a>
          <FeedbackDialog>
            <button
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-white/[0.06] py-2 text-[13px] font-semibold text-zinc-400 transition hover:bg-white/10 hover:text-zinc-200"
              type="button"
            >
              <LightbulbIcon size={14} />
              {t("sidebar.feedback")}
            </button>
          </FeedbackDialog>
        </div>

        {appVersion !== null && (
          <button
            className="block w-full pb-2 text-center font-mono text-xs text-ink-muted hover:text-zinc-400"
            onClick={() => onNavigate("support")}
          >
            {t("sidebar.version", { version: appVersion })}
          </button>
        )}
      </div>

      <div
        aria-hidden
        className="group absolute inset-y-0 -end-[3px] z-10 w-[7px] cursor-col-resize touch-none"
        onDoubleClick={() => setWidth(null)}
        onPointerCancel={endResize}
        onPointerDown={startResize}
        onPointerMove={moveResize}
        onPointerUp={endResize}
      >
        <div
          className={`mx-auto h-full w-px transition-colors duration-150 ${
            isResizing
              ? "bg-indigo-soft/50"
              : "bg-transparent group-hover:bg-indigo-soft/15"
          }`}
        />
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
      // Sized like Linear's sidebar: 13px labels, 16px icons, 28px rows.
      className={`group flex h-7 w-full items-center gap-2 rounded-lg px-[10px] text-start text-[13px] font-medium transition-[background-color,color,opacity] duration-150 ease-out ${
        isActive
          ? "bg-panel-raised text-white opacity-100"
          : "text-zinc-300 hover:bg-white/[0.055] hover:text-zinc-100"
      }`}
      onClick={() => onNavigate(item.id)}
    >
      {/* The selected icon is flagship green; the rest sit a step darker than their label. */}
      <item.icon
        className={
          isActive
            ? "text-[#2ef59c]"
            : "text-zinc-400 transition-colors duration-150 group-hover:text-zinc-200"
        }
        size={16}
      />
      <span className="truncate">{t(`sidebar.nav.${item.labelKey}`)}</span>
    </button>
  )
}
