import CitationChip from "./components/CitationChip"

function App() {
  return (
    <div className="app">
      <h1>Bangla Gov-Service Assistant</h1>
      <CitationChip
        doc="required_documents"
        excerpt="Documents needed to be carried during enrolment at Passport offices: 1. Printed application summary including appointment (if any). 2. Identification documents (NID card / Birth certificate - Original)."
      />
      <CitationChip
        doc="required_documents_detailed"
        excerpt="Documents Checklist for e-Passport Enrollment — Last updated: 21 October 2024."
      />
    </div>
  )
}

export default App