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

import { RuleTester } from "eslint"
import tseslint from "typescript-eslint"

import local from "./plugin.js"

const tester = new RuleTester({
  languageOptions: {
    parser: tseslint.parser,
    parserOptions: { ecmaFeatures: { jsx: true } },
  },
})
const { rules } = local

tester.run("ime-safe-keys", rules["ime-safe-keys"], {
  valid: [
    `const f = (e) => { if (e.nativeEvent.isComposing) return; if (e.key === "Enter") go() }`,
    `const f = (e) => { if (e.key === "Escape") close() }`,
  ],
  invalid: [
    {
      code: `const f = (e) => { if (e.key === "Enter") go() }`,
      errors: [{ messageId: "composing" }],
    },
    {
      code: `const f = (e) => { switch (e.key) { case "Tab": go() } }`,
      errors: [{ messageId: "composing" }],
    },
    {
      // Another handler's check doesn't cover this one.
      code: `const C = () => { const a = (e) => { if (e.isComposing) return }; const b = (e) => { if (e.key === "Enter") go() } }`,
      errors: [{ messageId: "composing" }],
    },
  ],
})

tester.run("button-name", rules["button-name"], {
  valid: [
    `<button>{t("save")}</button>`,
    `<button>{open ? t("hide") : t("show")}</button>`,
    `<button aria-label={label}>{reference}</button>`,
    `<button><Icon />{label}</button>`,
    `<button>{label ?? <><Icon />{t("go")}</>}</button>`,
    `<button>{label}</button>`,
    `<button>{children}</button>`,
  ],
  invalid: [
    { code: `<button>{reference}</button>`, errors: [{ messageId: "name" }] },
    { code: `<Button>{"›"}</Button>`, errors: [{ messageId: "name" }] },
  ],
})

tester.run("no-command-in-effect", rules["no-command-in-effect"], {
  valid: [
    `import { save } from "@/services/commands"; const f = () => save()`,
    `import type { CommandSender } from "@/services/commands"; useEffect(() => { CommandSender() })`,
    `import { save } from "./other"; useEffect(() => { save() })`,
  ],
  invalid: [
    {
      code: `import { suggest } from "@/services/commands"; useEffect(() => { suggest().then(set) }, [])`,
      errors: [{ messageId: "effect" }],
    },
    {
      code: `import * as commands from "@/services/commands"; React.useLayoutEffect(() => { void commands.refresh() })`,
      errors: [{ messageId: "effect" }],
    },
  ],
})

tester.run("disable-needs-reason", rules["disable-needs-reason"], {
  valid: [
    `// eslint-disable-next-line no-console -- the CLI prints\nconsole.log(1)`,
  ],
  invalid: [
    {
      code: `// eslint-disable-next-line no-console\nconsole.log(1)`,
      errors: [{ messageId: "reason" }],
    },
  ],
})

tester.run("faint-text-on-icons-only", rules["faint-text-on-icons-only"], {
  valid: [
    `<svg className="text-ink-faint" />`,
    `import { Check } from "lucide-react"; <Check className="text-ink-faint" />`,
    `<span className="text-ink-faint"><WarningIcon /></span>`,
    `<input className="placeholder:text-ink-faint" />`,
  ],
  invalid: [
    {
      code: `<p className="text-xs text-ink-faint">{t("hint")}</p>`,
      errors: [{ messageId: "faint" }],
    },
    {
      code: "<span className={`${a} hover:text-ink-faint`}>x</span>",
      errors: [{ messageId: "faint" }],
    },
  ],
})

tester.run("no-symbol-text", rules["no-symbol-text"], {
  valid: [`<p>{t("cost")} 2× ©</p>`],
  invalid: [
    { code: `<span>›</span>`, errors: [{ messageId: "symbol" }] },
    { code: `<span>{"⚠"}</span>`, errors: [{ messageId: "symbol" }] },
  ],
})

tester.run("no-hex-color", rules["no-hex-color"], {
  valid: [`<p className="text-ink" style={{ color: "var(--color-ink)" }} />`],
  invalid: [
    {
      code: `<p className="text-[#f4f4f6]" />`,
      errors: [{ messageId: "hex" }],
    },
    { code: `const C = { ink: "#fff" }`, errors: [{ messageId: "hex" }] },
    {
      code: `<p className="bg-[linear-gradient(#5b6fe8_0%,#fff_100%)]" />`,
      errors: [{ messageId: "hex" }],
    },
  ],
})
