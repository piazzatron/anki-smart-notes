import type { ReviewClaimState } from "@/types/api"

export type BannerPrompt = "review" | "discord" | null

export interface BannerPromptState {
  hasState: boolean
  didDismissReviewPrompt: boolean
  didDismissDiscordPrompt: boolean
  // Dismissed during this window session. Resets to false on the next open,
  // while the persisted `didDismiss*` flags carry over.
  reviewDismissedThisSession: boolean
  discordDismissedThisSession: boolean
}

/**
 * Chooses which prompt takes the single banner slot above the field list.
 *
 * Dismissing the review prompt leaves the slot empty for the rest of the
 * session: the Discord prompt only takes over on a later open, once the review
 * dismissal has persisted and `reviewDismissedThisSession` has reset.
 */
export const selectBannerPrompt = (state: BannerPromptState): BannerPrompt => {
  if (!state.hasState) return null

  if (!state.didDismissReviewPrompt && !state.reviewDismissedThisSession) {
    return "review"
  }

  // The review prompt held the slot this session; leave it empty until reopen.
  if (state.reviewDismissedThisSession) return null

  if (!state.didDismissDiscordPrompt && !state.discordDismissedThisSession) {
    return "discord"
  }

  return null
}

export type ReviewBannerKind = "offer" | "plain" | null

export interface ReviewBannerState {
  reviewFreeMonth: boolean
  offerUnlocked: boolean
  claimLoading: boolean
  claimState: ReviewClaimState | null
}

/**
 * Chooses what the review banner shows. While the `review_free_month` flag is
 * on, it waits for the user's first generation and for the server's answer,
 * then offers the free month to anyone who can still get it (or has a claim
 * pending). Everyone else, including when the server can't be reached, gets
 * the plain review ask.
 */
export const selectReviewBanner = (
  state: ReviewBannerState,
): ReviewBannerKind => {
  if (!state.reviewFreeMonth) return "plain"
  if (!state.offerUnlocked || state.claimLoading) return null
  return state.claimState === "available" || state.claimState === "claimed"
    ? "offer"
    : "plain"
}
