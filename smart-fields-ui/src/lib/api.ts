const API_URL = "http://127.0.0.1:8766/"
const API_VERSION = 1

type ApiResponse<T> = { result: T; error: null } | { result: null; error: string }

async function call<T>(action: string, params: Record<string, unknown> = {}): Promise<T> {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, version: API_VERSION, params }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = (await res.json()) as ApiResponse<T>
  if (data.error) throw new Error(data.error)
  return data.result as T
}

export type SmartFieldInfo = {
  prompt: string
  extras: {
    automatic?: boolean
    type?: "chat" | "tts" | "image"
  } | null
}

export const api = {
  ping: () => call<string>("ping"),
  listNoteTypes: () => call<string[]>("listNoteTypes"),
  getFields: (noteType: string) => call<string[]>("getFields", { noteType }),
  getSmartFields: (noteType: string) =>
    call<Record<string, SmartFieldInfo>>("getSmartFields", { noteType }),
  addSmartField: (params: { noteType: string; field: string; prompt: string }) =>
    call<boolean>("addSmartField", { ...params, type: "chat" }),
  removeSmartField: (params: { noteType: string; field: string }) =>
    call<boolean>("removeSmartField", params),
}
