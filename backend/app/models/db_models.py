import uuid
import enum
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class DomainEnum(str, enum.Enum):
    passport = "passport"
    nid = "nid"
    tax = "tax"
    utilities = "utilities"


class LanguageEnum(str, enum.Enum):
    bn = "bn"
    en = "en"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    domain = Column(Enum(DomainEnum), nullable=False)
    language = Column(Enum(LanguageEnum), nullable=False)
    confident = Column(Boolean, nullable=False)
    citations = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())