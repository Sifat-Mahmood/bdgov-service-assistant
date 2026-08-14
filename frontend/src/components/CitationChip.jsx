import { useState } from "react"

function CitationChip({ doc, excerpt }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="citation-chip">
      <button onClick={() => setExpanded(!expanded)}>
        📄 {doc}
      </button>
      {expanded && <p className="citation-excerpt">{excerpt}</p>}
    </div>
  )
}

export default CitationChip