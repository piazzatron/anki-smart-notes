import { ChatIcon, GalleryIcon, VolumeIcon } from "@/components/shared/Icons"
import type { SmartField } from "@/types/api"
import { useTranslation } from "react-i18next"

interface FieldTypeIconProps {
  fieldType: SmartField["fieldType"]
}

const ICONS = {
  chat: ChatIcon,
  image: GalleryIcon,
  tts: VolumeIcon,
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
      className="pointer-events-none inline-flex size-[22px] items-center justify-center text-ink-muted"
      role="img"
    >
      <Icon size={16} />
    </span>
  )
}
