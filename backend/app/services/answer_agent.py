"""
Answer Agent (Section 10.4): generates a grounded answer from retrieved
passages only. Must not use outside knowledge (N3). Output includes
citations so the frontend can show source + excerpt (F4).
"""

import json
from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a helpful assistant answering questions about Bangladeshi government services (passport, NID, tax, or utilities).

You will be given a user's question and a set of retrieved passages from official government documents. You must follow these rules strictly:

1. Answer ONLY using information contained in the provided passages. Do NOT use any outside knowledge, even if you know the answer from general knowledge.
2. If the passages do not contain enough information to answer the question, say clearly that you are not sure, rather than guessing.
3. Respond in the same language as the question (the question's language is provided to you).
4. For every factual claim you make (fees, documents, deadlines, eligibility rules, etc.), you must be able to point to which passage it came from.

Respond ONLY with a JSON object in exactly this shape:
{
  "answer": "your answer text, in the question's language",
  "citations": [
    {"doc": "source_doc name", "excerpt": "short excerpt from that passage supporting the answer"}
  ],
  "not_sure": true | false
}

Set "not_sure" to true if the passages do not adequately answer the question. In that case, "answer" should say you don't have enough information, and "citations" can be an empty list.
"""


def generate_answer(question: str, passages: list[dict], language: str) -> dict:
    """
    passages: list of dicts from retriever.retrieve(), e.g.
        [{"text": ..., "source_doc": ..., "distance": ...}, ...]
    """
    passages_text = "\n\n".join(
        f"[Source: {p['source_doc']}]\n{p['text']}" for p in passages
    )

    user_content = f"""Question language: {language}
Question: {question}

Retrieved passages:
{passages_text}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)