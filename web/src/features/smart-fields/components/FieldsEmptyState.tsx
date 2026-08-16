export const FieldsEmptyState = () => (
  <div className="smart-fields-empty">
    <div aria-hidden className="smart-fields-empty-illustration">
      <span className="smart-fields-empty-spark smart-fields-empty-spark-one">
        ✦
      </span>
      <span className="smart-fields-empty-spark smart-fields-empty-spark-two">
        ✦
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
          <span>FRONT</span>
          <span className="smart-fields-empty-card-dot" />
        </div>
        <div className="smart-fields-empty-card-prompt">bonjour</div>
        <div className="smart-fields-empty-card-divider" />
        <div className="smart-fields-empty-card-answer">
          <span className="smart-fields-empty-card-magic">✨</span>
          <span>Hello</span>
          <span className="smart-fields-empty-card-cursor" />
        </div>
      </div>
    </div>

    <h2 className="smart-fields-empty-title">
      Your notes are looking a little empty
    </h2>
    <p className="smart-fields-empty-copy">
      Add Smart Fields to add text, audio, and images to your cards.
    </p>
  </div>
)
