import { Button } from "@/components/ui/Button"
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
          💬
        </span>
        <span className="smart-fields-empty-bubble smart-fields-empty-bubble-audio">
          🔈
        </span>
        <span className="smart-fields-empty-bubble smart-fields-empty-bubble-image">
          🎨
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
            <span className="smart-fields-empty-card-magic">✨</span>
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
        className="smart-fields-empty-cta mt-5 h-auto shrink-0 !rounded-lg !border-[#1fd47d]/60 !bg-gradient-to-b !from-[#4cf0a8] !to-[#1fd47d] !px-8 !py-4 !text-base !font-extrabold !text-[#06281a] hover:!border-[#1fd47d]/60 hover:brightness-105"
        onClick={onCreate}
        variant="success"
      >
        {t("smartFields.newSmartField")}
      </Button>
    </div>
  )
}
