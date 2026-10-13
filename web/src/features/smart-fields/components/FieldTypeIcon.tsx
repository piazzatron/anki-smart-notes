import { ChatIcon, GalleryIcon, VolumeIcon } from "@/components/shared/Icons"
import type { SmartField } from "@/types/api"
import { useTranslation } from "react-i18next"

interface FieldTypeIconProps {
  fieldType: SmartField["fieldType"]
}

// Each type keeps its pastel so the list scans by type at a glance.
const ICONS = {
  chat: { Icon: ChatIcon, tint: "text-pastel-sky" },
  image: { Icon: GalleryIcon, tint: "text-pastel-butter" },
  tts: { Icon: VolumeIcon, tint: "text-pastel-pink" },
}

export const FieldTypeIcon = ({ fieldType }: FieldTypeIconProps) => (
  <FieldTypeIconLabel fieldType={fieldType} />
)

const FieldTypeIconLabel = ({ fieldType }: FieldTypeIconProps) => {
  const { t } = useTranslation()
  const { Icon, tint } = ICONS[fieldType]

  return (
    <span
      aria-label={t("smartFields.fieldTypeAriaLabel", {
        fieldType: t(`smartFields.fieldTypes.${fieldType}`),
      })}
      className={`pointer-events-none inline-flex size-[22px] items-center justify-center ${tint}`}
      role="img"
    >
      <Icon size={16} />
    </span>
  )
}
