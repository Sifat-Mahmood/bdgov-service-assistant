import { useState } from "react"
import { registerUser, loginUser } from "../api/client"

function AuthForm({ onLogin }) {
  const [mode, setMode] = useState("login") // "login" or "register"
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      if (mode === "register") {
        await registerUser(email, password)
        // Registration doesn't auto-login (per Section 11's contract), so
        // switch to login mode and let the user log in with the same credentials.
        setMode("login")
        setPassword("")
        setError("Account created. Please log in.")
      } else {
        const data = await loginUser(email, password)
        onLogin(data.access_token)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "..." : mode === "login" ? "Log in" : "Register"}
        </button>
      </form>
      {error && <p className="auth-message">{error}</p>}
      <button
        type="button"
        className="auth-toggle"
        onClick={() => {
          setMode(mode === "login" ? "register" : "login")
          setError(null)
        }}
      >
        {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
      </button>
    </div>
  )
}

export default AuthForm