import { useState } from "react"
import { sendChatMessage } from "./api/client"

function App() {
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleTestClick() {
    setError(null)
    setResult(null)
    try {
      const data = await sendChatMessage(
        "What documents do I need for a passport?",
        "test-session-1"
      )
      setResult(data)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="app">
      <h1>Bangla Gov-Service Assistant</h1>
      <button onClick={handleTestClick}>Test backend connection</button>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  )
}

export default App