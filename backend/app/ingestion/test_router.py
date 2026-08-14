import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.router_agent import route_question

test_questions = [
    # Clean baseline (should still work)
    "How much does a 5 year passport cost?",

    # NID vs passport — document overlap
    "What documents do I need to submit?",
    "Do I need my birth certificate for this?",
    "What's the process for a minor applicant?",

    # Tax vs utilities — billing/payment overlap
    "How do I pay my bill online?",
    "What happens if I miss the deadline?",

    # Genuinely generic / no service named
    "How long does it take to process?",
    "What's the fee?",

    # Out of scope but plausibly government-adjacent (trickier than land registration)
    "How do I renew my driving license?",
    "Can I track my application status online?",

    # Clean baseline other domains
    "আমি কীভাবে নতুন গ্যাস সংযোগের জন্য আবেদন করব?",
]

for q in test_questions:
    result = route_question(q)
    print(f"Q: {q}")
    print(f"A: {result}")
    print("-" * 50)