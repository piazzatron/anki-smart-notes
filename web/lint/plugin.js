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

/** Smart Notes' own lint rules for the web UI: the problems the frontend review kept
 * finding. Registered as `local` in eslint.config.js. */

const COMMANDS_MODULE = /(^@\/services\/commands$|\/services\/commands$)/
const EFFECT_HOOKS = new Set(["useEffect", "useLayoutEffect"])
const IME_KEYS = new Set(["Enter", "Tab"])
const ICON_MODULES = new Set(["lucide-react", "@/components/shared/Icons"])
// Emoji and the symbol blocks people reach for as icons (arrows, dingbats, shapes,
// guillemets, bullets). Copyright marks and the × in "2× cost" are ordinary text.
const SYMBOLS = /[\p{Extended_Pictographic}←-⇿⌀-⏿■-➿‹›«»•]/u
const TEXT_PROPS = /^(label|title|text|name|children)$/i
const PLAIN_MARKS = new Set(["©", "®", "™"])
// Not \b: Tailwind arbitrary values join parts with `_` (`#fff_100%`).
const HEX = /#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})(?![0-9a-f])/i

// Calls visit on node and every node under it.
const walk = (node, visit) => {
  visit(node)
  for (const [key, child] of Object.entries(node)) {
    if (key === "parent") continue
    for (const item of Array.isArray(child) ? child : [child])
      if (item?.type) walk(item, visit)
  }
}

const jsxName = (node) => (node.type === "JSXIdentifier" ? node.name : null)

const hasAttribute = (opening, names) =>
  opening.attributes.some(
    (attribute) =>
      attribute.type === "JSXSpreadAttribute" ||
      names.includes(attribute.name.name),
  )

const enclosingFunctions = (context, node) =>
  context.sourceCode
    .getAncestors(node)
    .filter((ancestor) => /Function/.test(ancestor.type))

const isKeyRead = (node) =>
  node.type === "MemberExpression" &&
  !node.computed &&
  node.property.name === "key"

const imeSafeKeys = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Enter and Tab handlers must ignore keys while an IME is composing. It can't tell a text input's handler from a list row's, so a row handler checks too (a no-op there).",
    },
    messages: {
      composing:
        'This handler acts on "{{key}}" but never checks isComposing, so it fires while someone is typing Japanese or Chinese with an IME. Return early on `event.nativeEvent.isComposing` (or `event.isComposing` for a DOM event).',
    },
    schema: [],
  },
  create(context) {
    const check = (node, key) => {
      // Only the handler itself counts: another handler's check doesn't cover this one.
      const handler = enclosingFunctions(context, node).at(-1)
      if (
        handler &&
        !context.sourceCode.getText(handler).includes("isComposing")
      )
        context.report({ node, messageId: "composing", data: { key } })
    }
    return {
      BinaryExpression(node) {
        if (!["===", "==", "!==", "!="].includes(node.operator)) return
        const [read, literal] = isKeyRead(node.left)
          ? [node.left, node.right]
          : [node.right, node.left]
        if (isKeyRead(read) && IME_KEYS.has(literal.value))
          check(node, literal.value)
      },
      SwitchCase(node) {
        if (
          isKeyRead(node.parent.discriminant) &&
          IME_KEYS.has(node.test?.value)
        )
          check(node, node.test.value)
      },
    }
  },
}

// An expression that renders words: a t() call, or a choice between them.
const isTranslatedText = (expression) => {
  if (expression.type === "CallExpression") {
    const callee = expression.callee
    return (
      (callee.type === "Identifier" && callee.name === "t") ||
      (callee.type === "MemberExpression" && callee.property.name === "t")
    )
  }
  if (expression.type === "ConditionalExpression")
    return (
      isTranslatedText(expression.consequent) &&
      isTranslatedText(expression.alternate)
    )
  if (expression.type === "LogicalExpression")
    return isTranslatedText(expression.right)
  // A prop that carries words by name: `{label}`, `{item.title}`, `{children}`.
  const name =
    expression.type === "MemberExpression"
      ? expression.property.name
      : expression.name
  return TEXT_PROPS.test(name ?? "")
}

const buttonName = {
  meta: {
    type: "problem",
    docs: {
      description:
        "A button whose only content is a JSX expression needs an aria-label",
    },
    messages: {
      name: "This button's only content is {{expression}}, which can be symbols or a raw value rather than words. Give it an aria-label that says what it does.",
    },
    schema: [],
  },
  create(context) {
    return {
      JSXElement(node) {
        if (!["button", "Button"].includes(jsxName(node.openingElement.name)))
          return
        if (
          hasAttribute(node.openingElement, ["aria-label", "aria-labelledby"])
        )
          return
        const content = node.children.filter(
          (child) => !(child.type === "JSXText" && child.value.trim() === ""),
        )
        const expressions = content.filter(
          (child) =>
            child.type === "JSXExpressionContainer" &&
            child.expression.type !== "JSXEmptyExpression",
        )
        if (expressions.length === 0 || expressions.length !== content.length)
          return
        // Words from t(), or elements (an icon and a label), give the button a name.
        const named = expressions.some((child) => {
          let hasElement = false
          walk(child.expression, (inner) => {
            if (inner.type === "JSXElement" || inner.type === "JSXFragment")
              hasElement = true
          })
          return hasElement || isTranslatedText(child.expression)
        })
        if (named) return
        context.report({
          node: node.openingElement,
          messageId: "name",
          data: { expression: context.sourceCode.getText(expressions[0]) },
        })
      },
    }
  },
}

const noCommandInEffect = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Server commands called from an effect need a disable comment saying when they fire",
    },
    messages: {
      effect:
        "{{name}}() calls the Anki/server backend from an effect, so it runs on every mount and dependency change, even when nobody sees the result (and some commands spend credits). Call it from an event handler, or, if the effect is right, add `// eslint-disable-next-line local/no-command-in-effect -- <when this fires>`.",
    },
    schema: [],
  },
  create(context) {
    const commands = new Set()
    const namespaces = new Set()

    const insideEffect = (node) =>
      context.sourceCode
        .getAncestors(node)
        .some(
          (ancestor) =>
            ancestor.type === "CallExpression" &&
            EFFECT_HOOKS.has(
              ancestor.callee.type === "MemberExpression"
                ? ancestor.callee.property.name
                : ancestor.callee.name,
            ),
        )

    return {
      ImportDeclaration(node) {
        if (
          node.importKind === "type" ||
          !COMMANDS_MODULE.test(node.source.value)
        )
          return
        for (const specifier of node.specifiers) {
          if (specifier.importKind === "type") continue
          if (specifier.type === "ImportNamespaceSpecifier")
            namespaces.add(specifier.local.name)
          else commands.add(specifier.local.name)
        }
      },
      CallExpression(node) {
        const { callee } = node
        const name =
          callee.type === "Identifier" && commands.has(callee.name)
            ? callee.name
            : callee.type === "MemberExpression" &&
                namespaces.has(callee.object.name)
              ? callee.property.name
              : null
        if (name && insideEffect(node))
          context.report({ node, messageId: "effect", data: { name } })
      },
    }
  },
}

const disableNeedsReason = {
  meta: {
    type: "suggestion",
    docs: { description: "Every eslint-disable comment says why" },
    messages: {
      reason: "Say why this rule is off: end the comment with ` -- <reason>`.",
    },
    schema: [],
  },
  create(context) {
    return {
      Program() {
        for (const comment of context.sourceCode.getAllComments()) {
          if (
            /^\s*eslint-disable/.test(comment.value) &&
            !comment.value.includes(" -- ")
          )
            context.report({ loc: comment.loc, messageId: "reason" })
        }
      },
    }
  },
}

// The literal class tokens a className attribute can produce.
const classTokens = (attribute) => {
  const tokens = []
  if (attribute.value)
    walk(attribute.value, (node) => {
      if (node.type === "Literal" && typeof node.value === "string")
        tokens.push(...node.value.split(/\s+/))
      else if (node.type === "TemplateElement")
        tokens.push(...node.value.cooked.split(/\s+/))
    })
  return tokens
}

const faintTextOnIconsOnly = {
  meta: {
    type: "problem",
    docs: {
      description: "text-ink-faint is for icons and placeholders, not text",
    },
    messages: {
      faint:
        "text-ink-faint is too dim to read: it's for icons, chevrons and `placeholder:` only. Use text-ink-muted for text.",
    },
    schema: [],
  },
  create(context) {
    const icons = new Set()
    const isIcon = (element) => {
      const tag = element.openingElement.name
      const name =
        tag.type === "JSXMemberExpression" ? tag.property.name : jsxName(tag)
      return name === "svg" || icons.has(name) || /Icon$/i.test(name ?? "")
    }
    return {
      ImportDeclaration(node) {
        if (ICON_MODULES.has(node.source.value))
          for (const specifier of node.specifiers)
            icons.add(specifier.local.name)
      },
      JSXAttribute(node) {
        if (node.name.name !== "className") return
        const faint = classTokens(node).some((token) =>
          /^(?!.*placeholder:)(.*:)?text-ink-faint(\/\d+)?$/.test(token),
        )
        if (!faint) return
        const element = node.parent.parent
        const content = element.children.filter(
          (child) => !(child.type === "JSXText" && child.value.trim() === ""),
        )
        const onlyIcons =
          content.length > 0 &&
          content.every((child) => child.type === "JSXElement" && isIcon(child))
        if (!isIcon(element) && !onlyIcons)
          context.report({ node, messageId: "faint" })
      },
    }
  },
}

const noSymbolText = {
  meta: {
    type: "problem",
    docs: { description: "No emoji or Unicode symbols as icons in JSX text" },
    messages: {
      symbol:
        '"{{symbol}}" is a Unicode symbol or emoji standing in for an icon. Use a Lucide icon or one from components/shared/Icons.tsx.',
    },
    schema: [],
  },
  create(context) {
    const check = (node, text) => {
      const symbol = [...text].find(
        (char) => SYMBOLS.test(char) && !PLAIN_MARKS.has(char),
      )
      if (!symbol) return
      // Point at the symbol itself, so a disable comment goes on its line.
      const start = context.sourceCode.getLocFromIndex(
        node.range[0] + context.sourceCode.getText(node).indexOf(symbol),
      )
      context.report({
        loc: { start, end: start },
        messageId: "symbol",
        data: { symbol },
      })
    }
    return {
      JSXText: (node) => check(node, node.value),
      "JSXExpressionContainer > Literal": (node) =>
        typeof node.value === "string" && check(node, node.value),
    }
  },
}

const noHexColor = {
  meta: {
    type: "problem",
    docs: {
      description: "No raw hex colors in class names, styles or constants",
    },
    messages: {
      hex: "Raw hex color. Use a palette token from globals.css (`text-ink`, or `var(--color-ink)` in a style), or ask before adding a color.",
    },
    schema: [],
  },
  create(context) {
    return {
      Literal: (node) =>
        typeof node.value === "string" &&
        HEX.test(node.value) &&
        context.report({ node, messageId: "hex" }),
      TemplateElement: (node) =>
        HEX.test(node.value.cooked) &&
        context.report({ node, messageId: "hex" }),
    }
  },
}

export default {
  rules: {
    "button-name": buttonName,
    "disable-needs-reason": disableNeedsReason,
    "faint-text-on-icons-only": faintTextOnIconsOnly,
    "ime-safe-keys": imeSafeKeys,
    "no-command-in-effect": noCommandInEffect,
    "no-hex-color": noHexColor,
    "no-symbol-text": noSymbolText,
  },
}
