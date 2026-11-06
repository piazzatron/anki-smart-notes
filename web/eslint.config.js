import { readFileSync } from "node:fs"

import js from "@eslint/js"
import betterTailwind from "eslint-plugin-better-tailwindcss"
import i18next from "eslint-plugin-i18next"
import jsxA11y from "eslint-plugin-jsx-a11y"
import react from "eslint-plugin-react"
import reactHooks from "eslint-plugin-react-hooks"
import globals from "globals"
import tseslint from "typescript-eslint"

import local from "./lint/plugin.js"

// Plain CSS classes defined in globals.css (`welcome-enter`, `select-item`), which
// Tailwind doesn't know about.
const CSS_CLASSES = [
  ...readFileSync("src/assets/styles/globals.css", "utf8").matchAll(
    /(?:^|[\s,}>+~(])\.([a-zA-Z_-][\w-]*)/gm,
  ),
].map(([, name]) => `^${name}$`)

// Class rules from skills/ui-design/SKILL.md. Each pattern matches a whole class,
// variants included (`hover:`, `rtl:`).
const VARIANTS = "^(?:[^\\s]*:)?"
const PHYSICAL = [
  ["-?ml", "ms"],
  ["-?mr", "me"],
  ["pl", "ps"],
  ["pr", "pe"],
  ["-?left", "start"],
  ["-?right", "end"],
  ["scroll-ml", "scroll-ms"],
  ["scroll-mr", "scroll-me"],
  ["scroll-pl", "scroll-ps"],
  ["scroll-pr", "scroll-pe"],
  ["rounded-l", "rounded-s"],
  ["rounded-r", "rounded-e"],
  ["rounded-tl", "rounded-ss"],
  ["rounded-tr", "rounded-se"],
  ["rounded-bl", "rounded-es"],
  ["rounded-br", "rounded-ee"],
  ["border-l", "border-s"],
  ["border-r", "border-e"],
  ["text-left", "text-start"],
  ["text-right", "text-end"],
]
const RESTRICTED_CLASSES = [
  {
    // Below 11.5px (also with a `/leading` or `!`): 12px is the smallest text, pills and cost labels are 11.5px.
    pattern: `${VARIANTS}text-\\[(?:\\d(?:\\.\\d+)?|10(?:\\.\\d+)?|11(?:\\.[0-4]\\d*)?)px\\](?:\\/\\S+)?!?$`,
    message: "Text below 12px (11.5px for pills and cost labels) is too small.",
  },
  {
    pattern: `${VARIANTS}uppercase$`,
    message: "No all-caps: labels are sentence case.",
  },
  {
    pattern: `${VARIANTS}(?:border|divide|ring|outline)(?:-[xytrblse]|-b[se])?-(?!spacing-)(?:white|black|[a-z]+-\\d{2,3}|\\[(?:#|rgb|hsl|color:).*\\])(?:\\/.*)?$`,
    message:
      "Hand-written line color. Dividers and region edges are `border-hairline` / `divide-hairline` (or components/ui/Divider.tsx).",
  },
  {
    pattern: `${VARIANTS}-?(?:[mp][xse]|start|end|inset-x|left|right)-\\[(22|76)px\\]$`,
    message:
      "Hard-coded $1px. Use the `hang` (22px) or `page` (76px) spacing tokens: `hang`, `-mx-hang`, `px-hang`, `px-page`.",
  },
  ...PHYSICAL.map(([physical, logical]) => ({
    pattern: `^((?:[^\\s]*:)?)(${physical.startsWith("-") ? "-?" : ""})${physical.replace("-?", "")}(-.*)?$`,
    fix: `$1$2${logical}$3`,
    message: `Physical direction breaks right-to-left layouts. Use \`${logical}\`.`,
  })),
]

export default tseslint.config(
  { ignores: ["dist", "src/web/static"] },
  { linterOptions: { reportUnusedDisableDirectives: "error" } },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      react,
      "react-hooks": reactHooks,
      "jsx-a11y": jsxA11y,
      local,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      ...Object.fromEntries(
        Object.keys(reactHooks.configs.recommended.rules).map((rule) => [
          rule,
          "error",
        ]),
      ),
      ...jsxA11y.flatConfigs.recommended.rules,
      "react/function-component-definition": [
        "error",
        {
          namedComponents: "arrow-function",
          unnamedComponents: "arrow-function",
        },
      ],
      "react/jsx-uses-react": "off",
      "react/react-in-jsx-scope": "off",
      "local/disable-needs-reason": "error",
      "local/ime-safe-keys": "error",
      "local/no-command-in-effect": "error",
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "JSXElement[openingElement.name.name=/^(button|Button)$/] JSXOpeningElement[name.name=/^h[1-6]$/]",
          message:
            "A heading inside a button is invalid HTML and drops out of heading navigation. Put the button inside the heading.",
        },
      ],
    },
  },
  {
    // The shipped UI follows skills/ui-design/SKILL.md; the dev mock panel doesn't.
    files: ["src/**/*.tsx"],
    ignores: ["src/dev/**"],
    plugins: { "better-tailwindcss": betterTailwind },
    settings: {
      "better-tailwindcss": {
        entryPoint: "src/assets/styles/globals.css",
        // Class strings also live in constants like CARD_CLASS and TONE_CLASSES.
        variables: [
          [
            "^(?:classNames?|classes|styles?|[A-Z0-9_]*(?:CLASS|CLASSES|CTA|CHIP|SURFACE))$",
            [{ match: "strings" }, { match: "objectValues" }],
          ],
        ],
      },
    },
    rules: {
      "better-tailwindcss/no-unknown-classes": [
        "error",
        { ignore: CSS_CLASSES },
      ],
      "better-tailwindcss/no-restricted-classes": [
        "error",
        { restrict: RESTRICTED_CLASSES },
      ],
      "local/button-name": "error",
      "local/faint-text-on-icons-only": "error",
      "local/no-symbol-text": "error",
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/**/*.test.{ts,tsx}", "src/dev/**"],
    rules: {
      "local/no-hex-color": "error",
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/**/*.test.{ts,tsx}", "src/dev/**"],
    plugins: { i18next },
    rules: {
      "i18next/no-literal-string": [
        "error",
        {
          mode: "jsx-only",
          "jsx-attributes": {
            include: [
              "alt",
              "aria-label",
              "ariaLabel",
              "description",
              "label",
              "note",
              "placeholder",
              "subtitle",
              "title",
            ],
          },
        },
      ],
    },
  },
)
