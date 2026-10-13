import {
  ChatSolidIcon,
  GallerySolidIcon,
  VolumeSolidIcon,
} from "@/components/shared/Icons"
import type { SmartField } from "@/types/api"
import { useTranslation } from "react-i18next"

interface FieldTypeIconProps {
  fieldType: SmartField["fieldType"]
}

const ICONS = {
  chat: ChatSolidIcon,
  image: GallerySolidIcon,
  tts: VolumeSolidIcon,
}

export const FieldTypeIcon = ({ fieldType }: FieldTypeIconProps) => (
  <FieldTypeIconLabel fieldType={fieldType} />
)

const FieldTypeIconLabel = ({ fieldType }: FieldTypeIconProps) => {
  const { t } = useTranslation()
  const Icon = ICONS[fieldType]

  return (
    <span
      aria-label={t("smartFields.fieldTypeAriaLabel", {
        fieldType: t(`smartFields.fieldTypes.${fieldType}`),
      })}
      className="pointer-events-none col-start-1 row-span-2 row-start-1 inline-flex size-5 items-center justify-center justify-self-end text-zinc-300"
      role="img"
    >
      <Icon size={20} />
    </span>
  )
}
