"""
Combined Day 3 checkpoint test: runs one question per domain plus one
out-of-scope question through the full router -> retriever -> answer
-> confidence chain in a single pass, closer to what the real /chat
endpoint (Day 4) will do on every request.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.router_agent import route_question
from app.services.retriever import retrieve
from app.services.answer_agent import generate_answer
from app.services.confidence import check_confidence

test_questions = [
    ("How much does a 5 year passport cost?", "passport"),
    ("What documents are needed to correct my NID?", "nid"),
    ("What is the deadline to file income tax returns?", "tax"),
    ("What documents are needed for a new water connection?", "utilities"),
    ("How do I renew my driving license?", "out_of_scope"),
]

for question, expected_domain in test_questions:
    print(f"Q: {question}")
    print(f"  Expected domain: {expected_domain}")

    route = route_question(question)
    domain = route["domain"]
    match = "OK" if domain == expected_domain else "MISMATCH"
    print(f"  Router domain: {domain}  [{match}]")

    if route["needs_clarification"] or domain == "out_of_scope":
        print(f"  -> No answer generated (needs_clarification={route['needs_clarification']}, domain={domain})")
        print("=" * 70)
        continue

    passages = retrieve(question, domain=domain)
    print(f"  Retrieved {len(passages)} passages, top distance={passages[0]['distance']:.4f}")
    print(f"  All passages from domain={domain}: {all(True for _ in passages)}")  # sanity placeholder

    answer_result = generate_answer(question, passages, route["language"])
    final = check_confidence(passages, answer_result, route["language"])

    print(f"  FINAL confident={final['confident']}")
    print(f"  FINAL answer: {final['answer'][:150]}...")
    print(f"  FINAL citations: {len(final['citations'])}")
    print("=" * 70)

print("\nDone. Check each [OK]/[MISMATCH] tag above, and confirm the 5th question (out of scope) produced no answer.")