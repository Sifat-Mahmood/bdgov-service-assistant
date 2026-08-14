import ConfidenceBadge from "./components/ConfidenceBadge"

function App() {
  return (
    <div className="app">
      <h1>Bangla Gov-Service Assistant</h1>
      <p>Confident answer: <ConfidenceBadge confident={true} /></p>
      <p>Uncertain answer: <ConfidenceBadge confident={false} /></p>
    </div>
  )
}

export default App