/*
 * Copyright (C) 2024 Michael Piazza
 *
 * This file is part of Smart Notes.
 *
 * Smart Notes is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

export const LANGUAGES = [
  { ankiCode: "en_US", bcp47: "en", flag: "🇺🇸", nativeName: "English" },
  { ankiCode: "af_ZA", bcp47: "af", flag: "🇿🇦", nativeName: "Afrikaans" },
  {
    ankiCode: "ms_MY",
    bcp47: "ms",
    flag: "🇲🇾",
    nativeName: "Bahasa Melayu",
  },
  { ankiCode: "ca_ES", bcp47: "ca", flag: "🇪🇸", nativeName: "Català" },
  { ankiCode: "da_DK", bcp47: "da", flag: "🇩🇰", nativeName: "Dansk" },
  { ankiCode: "de_DE", bcp47: "de", flag: "🇩🇪", nativeName: "Deutsch" },
  { ankiCode: "et_EE", bcp47: "et", flag: "🇪🇪", nativeName: "Eesti" },
  { ankiCode: "es_ES", bcp47: "es", flag: "🇪🇸", nativeName: "Español" },
  { ankiCode: "eo_UY", bcp47: "eo", flag: "🇺🇾", nativeName: "Esperanto" },
  { ankiCode: "eu_ES", bcp47: "eu", flag: "🇪🇸", nativeName: "Euskara" },
  { ankiCode: "fr_FR", bcp47: "fr", flag: "🇫🇷", nativeName: "Français" },
  { ankiCode: "gl_ES", bcp47: "gl", flag: "🇪🇸", nativeName: "Galego" },
  { ankiCode: "hr_HR", bcp47: "hr", flag: "🇭🇷", nativeName: "Hrvatski" },
  { ankiCode: "it_IT", bcp47: "it", flag: "🇮🇹", nativeName: "Italiano" },
  { ankiCode: "oc_FR", bcp47: "oc", flag: "🇫🇷", nativeName: "Lenga d'òc" },
  { ankiCode: "hu_HU", bcp47: "hu", flag: "🇭🇺", nativeName: "Magyar" },
  { ankiCode: "nl_NL", bcp47: "nl", flag: "🇳🇱", nativeName: "Nederlands" },
  { ankiCode: "nb_NO", bcp47: "nb", flag: "🇳🇴", nativeName: "Norsk" },
  { ankiCode: "pl_PL", bcp47: "pl", flag: "🇵🇱", nativeName: "Polski" },
  {
    ankiCode: "pt_BR",
    bcp47: "pt-BR",
    flag: "🇧🇷",
    nativeName: "Português Brasileiro",
  },
  {
    ankiCode: "pt_PT",
    bcp47: "pt-PT",
    flag: "🇵🇹",
    nativeName: "Português",
  },
  { ankiCode: "ro_RO", bcp47: "ro", flag: "🇷🇴", nativeName: "Română" },
  { ankiCode: "sk_SK", bcp47: "sk", flag: "🇸🇰", nativeName: "Slovenčina" },
  { ankiCode: "sl_SI", bcp47: "sl", flag: "🇸🇮", nativeName: "Slovenščina" },
  { ankiCode: "fi_FI", bcp47: "fi", flag: "🇫🇮", nativeName: "Suomi" },
  { ankiCode: "sv_SE", bcp47: "sv", flag: "🇸🇪", nativeName: "Svenska" },
  {
    ankiCode: "vi_VN",
    bcp47: "vi",
    flag: "🇻🇳",
    nativeName: "Tiếng Việt",
  },
  { ankiCode: "tr_TR", bcp47: "tr", flag: "🇹🇷", nativeName: "Türkçe" },
  { ankiCode: "zh_CN", bcp47: "zh-CN", flag: "🇨🇳", nativeName: "简体中文" },
  { ankiCode: "ja_JP", bcp47: "ja", flag: "🇯🇵", nativeName: "日本語" },
  { ankiCode: "zh_TW", bcp47: "zh-TW", flag: "🇹🇼", nativeName: "繁體中文" },
  { ankiCode: "ko_KR", bcp47: "ko", flag: "🇰🇷", nativeName: "한국어" },
  { ankiCode: "cs_CZ", bcp47: "cs", flag: "🇨🇿", nativeName: "Čeština" },
  { ankiCode: "el_GR", bcp47: "el", flag: "🇬🇷", nativeName: "Ελληνικά" },
  { ankiCode: "bg_BG", bcp47: "bg", flag: "🇧🇬", nativeName: "Български" },
  { ankiCode: "mn_MN", bcp47: "mn", flag: "🇲🇳", nativeName: "Монгол хэл" },
  { ankiCode: "ru_RU", bcp47: "ru", flag: "🇷🇺", nativeName: "Pусский язык" },
  { ankiCode: "sr_SP", bcp47: "sr", flag: "🇷🇸", nativeName: "Српски" },
  {
    ankiCode: "uk_UA",
    bcp47: "uk",
    flag: "🇺🇦",
    nativeName: "Українська мова",
  },
  { ankiCode: "hy_AM", bcp47: "hy", flag: "🇦🇲", nativeName: "Հայերեն" },
  { ankiCode: "he_IL", bcp47: "he", flag: "🇮🇱", nativeName: "עִבְרִית" },
  { ankiCode: "ar_SA", bcp47: "ar", flag: "🇸🇦", nativeName: "العربية" },
  { ankiCode: "fa_IR", bcp47: "fa", flag: "🇮🇷", nativeName: "فارسی" },
  { ankiCode: "th_TH", bcp47: "th", flag: "🇹🇭", nativeName: "ภาษาไทย" },
  { ankiCode: "ga_IE", bcp47: "ga", flag: "🇮🇪", nativeName: "Gaeilge" },
  {
    ankiCode: "be_BY",
    bcp47: "be",
    flag: "🇧🇾",
    nativeName: "Беларуская мова",
  },
  { ankiCode: "or_OR", bcp47: "or", flag: "🇮🇳", nativeName: "ଓଡ଼ିଆ" },
  { ankiCode: "tl", bcp47: "tl", flag: "🇵🇭", nativeName: "Filipino" },
] as const

export const CATALOG_LOCALES = LANGUAGES.map(({ bcp47 }) => bcp47)

export type CatalogLocale = (typeof LANGUAGES)[number]["bcp47"]
