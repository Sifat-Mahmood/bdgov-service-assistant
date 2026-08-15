import { useState } from "react"
import { sendChatMessage } from "../api/client"
import MessageBubble from "./MessageBubble"
import CitationChip from "./CitationChip"
import ConfidenceBadge from "./ConfidenceBadge"
import DomainTag from "./DomainTag"

function ChatWindow() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())

  async function handleSubmit(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question) return

    setMessages((prev) => [...prev, { role: "user", text: question }])
    setInput("")
    setLoading(true)

    try {
      const data = await sendChatMessage(question, sessionId)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          citations: data.citations,
          confident: data.confident,
          domain: data.domain,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-window">
      <div className="message-list">
        {messages.map((msg, i) => (
          <div key={i} className={`message-group ${msg.role === "user" ? "group-user" : "group-assistant"}`}>
            <MessageBubble role={msg.role} text={msg.text} />
            {msg.role === "assistant" && msg.domain && (
              <div className="message-meta">
                <DomainTag domain={msg.domain} />
                <ConfidenceBadge confident={msg.confident} />
              </div>
            )}
            {msg.role === "assistant" && msg.citations?.map((c, j) => (
              <CitationChip key={j} doc={c.doc} excerpt={c.excerpt} />
            ))}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about Passport, NID, Tax, or Utilities..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  )
}

export default ChatWindow