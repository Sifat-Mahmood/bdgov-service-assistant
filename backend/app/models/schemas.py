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

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str