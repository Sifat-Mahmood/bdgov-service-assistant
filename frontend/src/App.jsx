import { useState } from "react"
import "./App.css"
import AuthForm from "./components/AuthForm"
import ChatWindow from "./components/ChatWindow"

function App() {
  const [token, setToken] = useState(null)

  return (
    <div className="app">
      <h1>Bangla Gov-Service Assistant</h1>
      {!token ? (
        <AuthForm onLogin={setToken} />
      ) : (
        <p className="logged-in-notice">Logged in ✓</p>
      )}
      <ChatWindow token={token} />
    </div>
  )
}

export default App