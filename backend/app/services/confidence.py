"""
Confidence thresholding (Section 10.5).

DISTANCE_THRESHOLD is a placeholder starting value, not yet tuned.
Per Section 10.5, real tuning happens on Day 8 against the eval set.
Day 2/3 testing has only observed good-match distances in the
~0.22-0.37 range so far; 0.45 is set comfortably above that as a
starting cutoff, pending real bad-match examples to calibrate against.
"""

DISTANCE_THRESHOLD = 0.45

FALLBACK_MESSAGE = {
    "en": "I'm not confident I have accurate information to answer this. Please contact the relevant office directly: Passport (DIP) - epassport.gov.bd, NID - services.nidw.gov.bd, Tax (NBR) - nbr.gov.bd, or your utility provider.",
    "bn": "এই প্রশ্নের সঠিক উত্তর দেওয়ার জন্য আমার কাছে পর্যাপ্ত নির্ভরযোগ্য তথ্য নেই। অনুগ্রহ করে সরাসরি সংশ্লিষ্ট অফিসে যোগাযোগ করুন।",
}


def check_confidence(passages: list[dict], answer_result: dict, language: str) -> dict:
    """
    Combines retrieval-distance and model-self-reported signals into
    one final confidence decision.

    passages: from retriever.retrieve()
    answer_result: from answer_agent.generate_answer()
    language: "en" | "bn", used to pick the right fallback message

    Returns: {confident, answer, citations}
    - If confident: passes through the real answer + citations.
    - If not confident: overrides answer with the fallback message,
      citations cleared (nothing to cite if we're not trusting the answer).
    """
    top_distance = passages[0]["distance"] if passages else float("inf")
    distance_ok = top_distance <= DISTANCE_THRESHOLD
    model_self_reported_unsure = answer_result.get("not_sure", False)

    confident = distance_ok and not model_self_reported_unsure

    if confident:
        return {
            "confident": True,
            "answer": answer_result["answer"],
            "citations": answer_result["citations"],
        }
    else:
        return {
            "confident": False,
            "answer": FALLBACK_MESSAGE.get(language, FALLBACK_MESSAGE["en"]),
            "citations": [],
        }