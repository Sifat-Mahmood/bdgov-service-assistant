const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

export async function sendChatMessage(question, sessionId) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  })

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`)
  }

  return response.json()
}