const DOMAIN_LABELS = {
  passport: "Passport",
  nid: "NID",
  tax: "Tax",
  utilities: "Utilities",
}

function DomainTag({ domain }) {
  const label = DOMAIN_LABELS[domain] || domain

  return <span className="domain-tag">{label}</span>
}

export default DomainTag