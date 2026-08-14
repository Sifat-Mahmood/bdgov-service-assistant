import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.router_agent import route_question
from app.services.retriever import retrieve
from app.services.answer_agent import generate_answer

test_questions = [
    "How much does a 5 year passport cost?",
    "আমার এনআইডি সংশোধন করতে কী কী কাগজ লাগবে?",
    "What is the deadline to file income tax returns?",
]

for q in test_questions:
    print(f"Q: {q}")

    route = route_question(q)
    print(f"  Router: domain={route['domain']}, language={route['language']}, needs_clarification={route['needs_clarification']}")

    if route["needs_clarification"]:
        print(f"  -> Clarification needed: {route['clarification_question']}")
        print("=" * 70)
        continue

    if route["domain"] == "out_of_scope":
        print("  -> Out of scope, no answer generated.")
        print("=" * 70)
        continue

    passages = retrieve(q, domain=route["domain"])
    print(f"  Retrieved {len(passages)} passages, top distance={passages[0]['distance']:.4f}")

    result = generate_answer(q, passages, route["language"])
    print(f"  Answer: {result['answer']}")
    print(f"  Not sure: {result['not_sure']}")
    print(f"  Citations:")
    for c in result["citations"]:
        print(f"    - {c['doc']}: {c['excerpt'][:100]}...")
    print("=" * 70)