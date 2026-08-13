import type {
  ChatDefaultsSavePayload,
  CommandName,
  CommandResponse,
  FeedbackSendPayload,
  ImageDefaultsSavePayload,
  ImagePromptTestArgs,
  MediaTestResult,
  PromptGenerateArgs,
  PromptGenerateResult,
  SaveTestResultPayload,
  Settings,
  SmartField,
  SmartFieldCreatePayload,
  SmartFieldDeletePayload,
  SmartFieldUpdatePayload,
  TextPromptTestArgs,
  TextPromptTestResult,
  TTSDefaultsSavePayload,
  TTSPromptTestArgs,
  TTSMediaTestResult,
  UiOpenBrowserPayload,
} from "@/types/api"

import { bootOptions } from "@/lib/boot"

export type CommandSender = <Result = void>(
  command: CommandName,
  payload: object,
) => Promise<Result>

let sendCommand: CommandSender = sendCommandToAnki

export const setCommandSender = (sender: CommandSender): void => {
  sendCommand = sender
}

export const setSmartFieldEnabled = async (
  field: SmartField,
  enabled: boolean,
): Promise<void> => {
  await updateSmartField({ ...field, enabled })
}

export const createSmartField = async (
  field: SmartFieldCreatePayload,
): Promise<void> => {
  await sendCommand("smartFields.create", field)
}

export const updateSmartField = async (
  field: SmartFieldUpdatePayload,
): Promise<void> => {
  await sendCommand("smartFields.update", field)
}

export const deleteSmartField = async (field: SmartField): Promise<void> => {
  await sendCommand("smartFields.delete", {
    id: field.id,
  } satisfies SmartFieldDeletePayload)
}

export const saveChatDefaults = async (
  defaults: ChatDefaultsSavePayload,
): Promise<void> => {
  await sendCommand("defaults.chat.save", defaults)
}

export const saveImageDefaults = async (
  defaults: ImageDefaultsSavePayload,
): Promise<void> => {
  await sendCommand("defaults.image.save", defaults)
}

export const saveTTSDefaults = async (
  defaults: TTSDefaultsSavePayload,
): Promise<void> => {
  await sendCommand("defaults.tts.save", defaults)
}

export const saveSettings = async (settings: Settings): Promise<void> => {
  await sendCommand("settings.save", settings)
}

export const generatePrompt = async (
  args: PromptGenerateArgs,
): Promise<PromptGenerateResult> =>
  sendCommand<PromptGenerateResult>("prompts.generate", args)

export const sendFeedback = async (
  payload: FeedbackSendPayload,
): Promise<void> => {
  await sendCommand("support.sendFeedback", payload)
}

export const logout = async (): Promise<void> => {
  await sendCommand("auth.logout", {})
}

export const testTextPrompt = async (
  args: TextPromptTestArgs,
): Promise<TextPromptTestResult> =>
  sendCommand<TextPromptTestResult>("prompts.test", args)

export const testImagePrompt = async (
  args: ImagePromptTestArgs,
): Promise<MediaTestResult> => sendCommand<MediaTestResult>("images.test", args)

export const testTTSPrompt = async (
  args: TTSPromptTestArgs,
): Promise<TTSMediaTestResult> =>
  sendCommand<TTSMediaTestResult>("tts.test", args)

export const saveTestResultToCard = async (
  payload: SaveTestResultPayload,
): Promise<void> => {
  await sendCommand("notes.saveTestResult", payload)
}

export const openAnkiBrowser = async (): Promise<void> => {
  await sendCommand("ui.openBrowser", {} satisfies UiOpenBrowserPayload)
}

async function sendCommandToAnki<Result = void>(
  command: CommandName,
  payload: object,
): Promise<Result> {
  const response = await fetch("/api/command", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-Token": bootOptions.token,
    },
    body: JSON.stringify({ command, payload }),
  })
  const result = (await response.json()) as CommandResponse

  if (!response.ok || !result.ok) {
    throw new Error(
      result.error ?? `Command failed with status ${response.status}`,
    )
  }

  return result.result as Result
}
