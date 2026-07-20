import { Image, MessageSquareText, Volume2 } from "lucide-react"

import type { SmartField } from "../types"

interface FieldTypeIconProps {
  fieldType: SmartField["fieldType"]
}

const ICONS = {
  chat: { icon: MessageSquareText, classes: "text-indigo-soft" },
  tts: { icon: Volume2, classes: "text-mint" },
  image: { icon: Image, classes: "text-amber" },
}

export const FieldTypeIcon = ({ fieldType }: FieldTypeIconProps) => {
  const { icon: Icon, classes } = ICONS[fieldType]

  return (
    <span
      aria-label={`${fieldType} Smart Field`}
      className={`inline-flex size-[22px] items-center justify-center ${classes}`}
      role="img"
    >
      <Icon aria-hidden className="size-[15px]" />
    </span>
  )
}
