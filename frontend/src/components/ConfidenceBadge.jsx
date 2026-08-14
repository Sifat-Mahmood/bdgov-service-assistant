function ConfidenceBadge({ confident }) {
  return (
    <span className={`confidence-badge ${confident ? "confidence-high" : "confidence-low"}`}>
      {confident ? "✓ Confident" : "⚠ Not sure"}
    </span>
  )
}

export default ConfidenceBadge