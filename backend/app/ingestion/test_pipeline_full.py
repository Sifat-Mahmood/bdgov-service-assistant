import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.router_agent import route_question
from app.services.retriever import retrieve
from app.services.answer_agent import generate_answer
from app.services.confidence import check_confidence

test_questions = [
    "How much does a 5 year passport cost?",
    "How do I file a billing complaint for my electricity connection?",  # expected weak coverage
]

for q in test_questions:
    print(f"Q: {q}")

    route = route_question(q)
    print(f"  Router: domain={route['domain']}, language={route['language']}")

    if route["needs_clarification"] or route["domain"] == "out_of_scope":
        print(f"  -> Skipped (clarification or out of scope)")
        print("=" * 70)
        continue

    passages = retrieve(q, domain=route["domain"])
    print(f"  Top distance={passages[0]['distance']:.4f}")

    answer_result = generate_answer(q, passages, route["language"])
    print(f"  Model self-reported not_sure={answer_result['not_sure']}")

    final = check_confidence(passages, answer_result, route["language"])
    print(f"  FINAL confident={final['confident']}")
    print(f"  FINAL answer: {final['answer']}")
    print(f"  FINAL citations: {len(final['citations'])} citation(s)")
    print("=" * 70)