from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services.router_agent import route_question
from app.services.retriever import retrieve
from app.services.answer_agent import generate_answer
from app.services.confidence import check_confidence

router = APIRouter()

GENERIC_ERROR_MESSAGE = (
    "Sorry, something went wrong while processing your question. "
    "Please try again in a few minutes."
)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
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

    return ChatResponse(
        answer=final["answer"],
        citations=final["citations"],
        confident=final["confident"],
        domain=route["domain"],
    )