// The plan card and the Discord/Feedback strip stop fitting below this.
export const MIN_SIDEBAR_WIDTH = 192
export const MAX_SIDEBAR_WIDTH = 400

// The sidebar sits at the inline start, so in RTL its resize edge is on the
// left and dragging left widens it.
export const resizeSidebar = (
  startWidth: number,
  pointerDeltaX: number,
  direction: "ltr" | "rtl",
): number => {
  const width =
    startWidth + (direction === "rtl" ? -pointerDeltaX : pointerDeltaX)
  return Math.round(
    Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, width)),
  )
}
