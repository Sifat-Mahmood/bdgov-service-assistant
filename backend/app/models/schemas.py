from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    question: str
    session_id: str
    language: Optional[str] = None  # optional hint from frontend; not yet used to override auto-detection


class Citation(BaseModel):
    doc: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confident: bool
    domain: str

