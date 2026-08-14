import type { SmartField } from "@/types/api"

interface FieldTypeIconProps {
  fieldType: SmartField["fieldType"]
}

const ICONS = {
  chat: "💬",
  image: "🎨",
  tts: "🔈",
}

export const FieldTypeIcon = ({ fieldType }: FieldTypeIconProps) => (
  <span
    aria-label={`${fieldType} Smart Field`}
    className="pointer-events-none inline-flex size-[22px] items-center justify-center text-[15px]"
    role="img"
  >
    {ICONS[fieldType]}
  </span>
)
