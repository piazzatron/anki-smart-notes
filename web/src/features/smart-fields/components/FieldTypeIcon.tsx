import type { SmartField } from "@/types/api"
import { useTranslation } from "react-i18next"

interface FieldTypeIconProps {
  fieldType: SmartField["fieldType"]
}

const ICONS = {
  chat: "💬",
  image: "🎨",
  tts: "🔈",
}

export const FieldTypeIcon = ({ fieldType }: FieldTypeIconProps) => (
  <FieldTypeIconLabel fieldType={fieldType} />
)

const FieldTypeIconLabel = ({ fieldType }: FieldTypeIconProps) => {
  const { t } = useTranslation()

  return (
    <span
      aria-label={t("smartFields.fieldTypeAriaLabel", {
        fieldType: t(`smartFields.fieldTypes.${fieldType}`),
      })}
      className="pointer-events-none inline-flex size-[22px] items-center justify-center text-[15px]"
      role="img"
    >
      {ICONS[fieldType]}
    </span>
  )
}
