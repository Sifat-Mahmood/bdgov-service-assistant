function MessageBubble({ role, text }) {
  const isUser = role === "user"

  return (
    <div className={`message-bubble ${isUser ? "message-user" : "message-assistant"}`}>
      <p>{text}</p>
    </div>
  )
}

export default MessageBubble