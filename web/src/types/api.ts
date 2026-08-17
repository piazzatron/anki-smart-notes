/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Smart Notes is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Smart Notes. If not, see <https://www.gnu.org/licenses/>.
 */

// The Smart Notes API — canonical types for the plugin↔webview contract:
// every SSE event payload (`state`, `catalog`, `anki.browserSelectionChanged`)
// and every `POST /api/command` payload. Mirrors `src/web/dto.py` on the Python
// side. Presentation and app types do not belong here.

export type LegacyPlanId =
  "free" | "free_mini_1" | "small1" | "medium1" | "large1"
export type PlanType = "trial" | "freemium" | "small" | "medium" | "large"
export type PlanName = "Free Trial" | "Free" | "Lite" | "Standard" | "Pro"

export interface PlanInfo {
  /** @deprecated Use planType. Retained for compatibility with older clients. */
  planId: LegacyPlanId
  planType: PlanType
  planName: PlanName
  notesUsed: number | null
  notesLimit: number | null
  daysLeft: number
  textCreditsUsed: number
  textCreditsCapacity: number
  voiceCreditsUsed: number
  voiceCreditsCapacity: number
  imageCreditsUsed: number
  imageCreditsCapacity: number
  totalCreditsUsed: number
  totalCreditsCapacity: number
}

export type AccountState =
  | {
      status: "LOADING" | "UNAUTHENTICATED"
      plan: null
      email: null
    }
  | {
      status: "AUTHENTICATED"
      plan: PlanInfo
      email: string
    }

export interface ChatSmartFieldSettings {
  promptText: string
  provider: string
  model: string
  reasoningLevel: string
  webSearchEnabled: boolean
  usesDefaultGenerationSettings: boolean
}

export interface TTSSmartFieldSettings {
  sourceFieldName: string
  provider: string
  model: string
  voiceId: string
  usesDefaultGenerationSettings: boolean
}

export interface ImageSmartFieldSettings {
  promptText: string
  provider: string
  model: string
  usesDefaultGenerationSettings: boolean
}

export interface SmartFieldBase {
  id: string
  noteTypeId: number
  deckId: number
  targetFieldName: string
  enabled: boolean
}

export type SmartField =
  | (SmartFieldBase & {
      fieldType: "chat"
      settings: ChatSmartFieldSettings
    })
  | (SmartFieldBase & { fieldType: "tts"; settings: TTSSmartFieldSettings })
  | (SmartFieldBase & {
      fieldType: "image"
      settings: ImageSmartFieldSettings
    })

export interface NoteType {
  id: number
  name: string
  fields: string[]
}

export interface Deck {
  id: number
  name: string
}

export interface ChatGenerationSettings {
  provider: string
  model: string
  reasoningLevel: string
  webSearchEnabled: boolean
}

export interface TTSGenerationSettings {
  provider: string
  model: string
  voiceId: string
}

export interface ImageGenerationSettings {
  provider: string
  model: string
}

export interface GenerationDefaults {
  chat: ChatGenerationSettings
  tts: TTSGenerationSettings
  image: ImageGenerationSettings
}

export interface Settings {
  generateAtReview: boolean
  regenerateWhenBatching: boolean
  debug: boolean
  legacyOpenAiEnabled: boolean
  legacyOpenAiKey: string | null
  legacyOpenAiModel: string
  legacyOpenAiHost: string | null
  showWizardCompletion: boolean
  didDismissReviewPrompt: boolean
  didDismissDiscordPrompt: boolean
}

export interface FeatureFlags {
  reviewFreeMonth: boolean
}

export interface AppState {
  appVersion: string
  smartFields: SmartField[]
  noteTypes: NoteType[]
  decks: Deck[]
  globalDeckId: number
  account: AccountState
  featureFlags: FeatureFlags
  defaults: GenerationDefaults
  settings: Settings
}

export interface CatalogModel {
  id: string
  provider: string
}

export interface ChatModelCatalog {
  providers: string[]
  models: CatalogModel[]
  reasoningLevels: string[]
}

export interface ImageModelCatalog {
  providers: string[]
  models: CatalogModel[]
}

export interface Catalog {
  chat: ChatModelCatalog
  image: ImageModelCatalog
}

export interface VoiceCatalogItem {
  provider: string
  voiceId: string
  model: string
  name: string
  gender: "Male" | "Female" | "All"
  language: string
  priceTier: "free" | "low" | "standard" | "high" | "ultra-high"
}

export interface VoiceCatalog {
  voices: VoiceCatalogItem[]
}

export interface SelectedNote {
  cardId: number
  id: number
  noteTypeId: number
  deckId: number | null
  fields: Record<string, string>
}

export type Selection = { note: SelectedNote } | { note: null; count: number }

export type CommandName =
  | "account.refresh"
  | "auth.exchangeCode"
  | "smartFields.create"
  | "smartFields.update"
  | "smartFields.delete"
  | "defaults.save"
  | "defaults.chat.save"
  | "defaults.image.save"
  | "defaults.tts.save"
  | "prompts.test"
  | "images.test"
  | "tts.test"
  | "notes.saveTestResult"
  | "settings.save"
  | "prompts.generate"
  | "support.sendFeedback"
  | "auth.logout"
  | "ui.openBrowser"

export type SmartFieldCreatePayload =
  | Omit<Extract<SmartField, { fieldType: "chat" }>, "id">
  | Omit<Extract<SmartField, { fieldType: "tts" }>, "id">
  | Omit<Extract<SmartField, { fieldType: "image" }>, "id">

export type SmartFieldUpdatePayload = SmartField

export interface SmartFieldDeletePayload {
  id: string
}

export interface AuthExchangeCodePayload {
  code: string
}

export type GenerationDefaultsSavePayload = GenerationDefaults

export type ChatDefaultsSavePayload = ChatGenerationSettings
export type ImageDefaultsSavePayload = ImageGenerationSettings
export type TTSDefaultsSavePayload = TTSGenerationSettings

export interface TextPromptTestArgs {
  cardId?: number
  prompt: string
  settings: ChatGenerationSettings
}

export interface TextPromptTestResult {
  text: string
  resultToken?: string
}

export interface PromptGenerateArgs {
  noteTypeId: number
  deckId: number
  targetFieldName: string
  fieldType: "chat" | "image"
  generationPrompt: string
}

export interface PromptGenerateResult {
  prompt: string
}

export interface FeedbackSendPayload {
  message: string
}

export interface ImagePromptTestArgs {
  cardId?: number
  prompt: string
  settings: ImageGenerationSettings
}

export interface TTSPromptTestArgs {
  cardId?: number
  text: string
  settings: TTSGenerationSettings
}

export interface TTSMediaTestResult {
  dataUrl: string
  resultToken?: string
}

/** A card-backed media test: the token names the artifact a save may write back. */
export interface MediaTestResult {
  dataUrl: string
  resultToken?: string
}

export interface SaveTestResultPayload {
  token: string
  cardId: number
  fieldName: string
}

export type UiOpenBrowserPayload = Record<string, never>

export interface CommandResponse {
  ok: boolean
  error?: string
  result?: unknown
}
