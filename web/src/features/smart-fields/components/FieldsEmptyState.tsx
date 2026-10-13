import { Button } from "@/components/ui/Button"
import {
  ChatIcon,
  GalleryIcon,
  SparklesIcon,
  VolumeIcon,
} from "@/components/shared/Icons"
import { useTranslation } from "react-i18next"

interface FieldsEmptyStateProps {
  onCreate: () => void
}

export const FieldsEmptyState = ({ onCreate }: FieldsEmptyStateProps) => {
  const { t } = useTranslation()

  return (
    <div className="smart-fields-empty">
      <div aria-hidden className="smart-fields-empty-illustration">
        <span className="smart-fields-empty-spark smart-fields-empty-spark-one">
          {t("smartFields.emptyState.spark")}
        </span>
        <span className="smart-fields-empty-spark smart-fields-empty-spark-two">
          {t("smartFields.emptyState.spark")}
        </span>
        <span className="smart-fields-empty-bubble smart-fields-empty-bubble-text">
          <ChatIcon size={20} />
        </span>
        <span className="smart-fields-empty-bubble smart-fields-empty-bubble-audio">
          <VolumeIcon size={20} />
        </span>
        <span className="smart-fields-empty-bubble smart-fields-empty-bubble-image">
          <GalleryIcon size={20} />
        </span>

        <div className="smart-fields-empty-card">
          <div className="smart-fields-empty-card-topline">
            <span>{t("smartFields.emptyState.exampleField")}</span>
            <span className="smart-fields-empty-card-dot" />
          </div>
          <div className="smart-fields-empty-card-prompt">
            {t("smartFields.emptyState.examplePrompt")}
          </div>
          <div className="smart-fields-empty-card-divider" />
          <div className="smart-fields-empty-card-answer">
            <SparklesIcon size={13} />
            <span>{t("smartFields.emptyState.exampleAnswer")}</span>
            <span className="smart-fields-empty-card-cursor" />
          </div>
        </div>
      </div>

      <h2 className="smart-fields-empty-title">
        {t("smartFields.emptyState.title")}
      </h2>
      <p className="smart-fields-empty-copy">
        {t("smartFields.emptyState.description")}
      </p>
      <Button
        className="smart-fields-empty-cta relative mt-5 h-auto shrink-0 !rounded-lg !border-[#1fd47d]/60 !bg-gradient-to-b !from-[#4cf0a8] !to-[#1fd47d] !px-12 !py-4 !text-base !font-extrabold !text-[#06281a] hover:!border-[#1fd47d]/60 hover:brightness-105"
        onClick={onCreate}
        variant="success"
      >
        <SparklesIcon
          className="absolute start-4 top-1/2 -translate-y-1/2"
          size={18}
        />
        {t("smartFields.newSmartField")}
      </Button>
    </div>
  )
}
