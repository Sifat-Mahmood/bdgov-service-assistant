import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.retriever import retrieve

test_cases = [
    ("How much does a 5 year passport cost?", "passport"),
    ("What documents do I need to correct my NID?", "nid"),
    ("What is the deadline to file income tax returns?", "tax"),
    ("What documents are needed for a new electricity connection?", "utilities"),
]

for question, domain in test_cases:
    results = retrieve(question, domain)
    print(f"Q: {question}  [domain={domain}]")
    for i, r in enumerate(results):
        print(f"  [{i+1}] source={r['source_doc']} | distance={r['distance']:.4f}")
        print(f"      {r['text'][:120]}...")
    print("-" * 60)