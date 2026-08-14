from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models.schemas import ChatRequest, ChatResponse
from app.services.router_agent import route_question
from app.services.retriever import retrieve
from app.services.answer_agent import generate_answer
from app.services.confidence import check_confidence

from app.db.session import get_db
from app.models.db_models import ChatMessage
from app.services.auth_service import decode_access_token

router = APIRouter()

GENERIC_ERROR_MESSAGE = (
    "Sorry, something went wrong while processing your question. "
    "Please try again in a few minutes."
)

optional_bearer = HTTPBearer(auto_error=False)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(optional_bearer),
):
    user_id = None
    if credentials is not None:
        payload = decode_access_token(credentials.credentials)
        if payload is not None:
            user_id = payload["sub"]

    try:
        route = route_question(request.question)
    except Exception as e:
        print(f"[/chat error] {e}")
        return ChatResponse(
            answer=GENERIC_ERROR_MESSAGE,
            citations=[],
            confident=False,
            domain="out_of_scope",
        )

    if route["needs_clarification"] or route["domain"] == "out_of_scope":
        return ChatResponse(
            answer=route["clarification_question"] or "I'm sorry, this is outside what I can help with (passport, NID, tax, or utilities).",
            citations=[],
            confident=False,
            domain=route["domain"],
        )

    try:
        passages = retrieve(request.question, domain=route["domain"])
        answer_result = generate_answer(request.question, passages, route["language"])
        final = check_confidence(passages, answer_result, route["language"])
    except Exception as e:
        print(f"[/chat error] {e}")
        return ChatResponse(
            answer=GENERIC_ERROR_MESSAGE,
            citations=[],
            confident=False,
            domain=route["domain"],
        )

    try:
        db_message = ChatMessage(
            user_id=user_id,
            session_id=request.session_id,
            question=request.question,
            answer=final["answer"],
            domain=route["domain"],
            language=route["language"],
            confident=final["confident"],
            citations=final["citations"],
        )
        db.add(db_message)
        db.commit()
    except Exception as e:
        print(f"[/chat DB logging error] {e}")
        db.rollback()

    return ChatResponse(
        answer=final["answer"],
        citations=final["citations"],
        confident=final["confident"],
        domain=route["domain"],
    )