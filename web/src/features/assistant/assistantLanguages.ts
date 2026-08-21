export interface AssistantLanguage {
  /** Stored in the database and sent to the backend. */
  code: string
  label: string
  flag: string
}

export const AUTO_RESPONSE_LANGUAGE = "auto"

/**
 * The languages the assistant can be told to reply in, alphabetical after the
 * default. Flags are a rough visual cue, not a claim about where a language is
 * spoken.
 */
export const ASSISTANT_LANGUAGES: AssistantLanguage[] = [
  { code: AUTO_RESPONSE_LANGUAGE, label: "Match what I write", flag: "🌐" },
  { code: "ar", label: "Arabic", flag: "🇸🇦" },
  { code: "bn", label: "Bengali", flag: "🇧🇩" },
  { code: "bg", label: "Bulgarian", flag: "🇧🇬" },
  { code: "zh-Hans", label: "Chinese (Simplified)", flag: "🇨🇳" },
  { code: "zh-Hant", label: "Chinese (Traditional)", flag: "🇹🇼" },
  { code: "hr", label: "Croatian", flag: "🇭🇷" },
  { code: "cs", label: "Czech", flag: "🇨🇿" },
  { code: "da", label: "Danish", flag: "🇩🇰" },
  { code: "nl", label: "Dutch", flag: "🇳🇱" },
  { code: "en", label: "English", flag: "🇺🇸" },
  { code: "fil", label: "Filipino", flag: "🇵🇭" },
  { code: "fi", label: "Finnish", flag: "🇫🇮" },
  { code: "fr", label: "French", flag: "🇫🇷" },
  { code: "de", label: "German", flag: "🇩🇪" },
  { code: "el", label: "Greek", flag: "🇬🇷" },
  { code: "he", label: "Hebrew", flag: "🇮🇱" },
  { code: "hi", label: "Hindi", flag: "🇮🇳" },
  { code: "hu", label: "Hungarian", flag: "🇭🇺" },
  { code: "is", label: "Icelandic", flag: "🇮🇸" },
  { code: "id", label: "Indonesian", flag: "🇮🇩" },
  { code: "it", label: "Italian", flag: "🇮🇹" },
  { code: "ja", label: "Japanese", flag: "🇯🇵" },
  { code: "ko", label: "Korean", flag: "🇰🇷" },
  { code: "no", label: "Norwegian", flag: "🇳🇴" },
  { code: "fa", label: "Persian", flag: "🇮🇷" },
  { code: "pl", label: "Polish", flag: "🇵🇱" },
  { code: "pt", label: "Portuguese", flag: "🇵🇹" },
  { code: "pt-BR", label: "Portuguese (Brazil)", flag: "🇧🇷" },
  { code: "ro", label: "Romanian", flag: "🇷🇴" },
  { code: "ru", label: "Russian", flag: "🇷🇺" },
  { code: "sr", label: "Serbian", flag: "🇷🇸" },
  { code: "sk", label: "Slovak", flag: "🇸🇰" },
  { code: "es", label: "Spanish", flag: "🇪🇸" },
  { code: "sw", label: "Swahili", flag: "🇰🇪" },
  { code: "sv", label: "Swedish", flag: "🇸🇪" },
  { code: "th", label: "Thai", flag: "🇹🇭" },
  { code: "tr", label: "Turkish", flag: "🇹🇷" },
  { code: "uk", label: "Ukrainian", flag: "🇺🇦" },
  { code: "ur", label: "Urdu", flag: "🇵🇰" },
  { code: "vi", label: "Vietnamese", flag: "🇻🇳" },
]

/** Falls back to Auto so an unknown stored code still renders something. */
export const findAssistantLanguage = (code: string): AssistantLanguage =>
  ASSISTANT_LANGUAGES.find((language) => language.code === code) ??
  ASSISTANT_LANGUAGES[0]
