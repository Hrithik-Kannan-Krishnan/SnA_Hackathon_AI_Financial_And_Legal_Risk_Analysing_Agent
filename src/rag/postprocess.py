from __future__ import annotations

import re

MONTH_DATE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{1,2},\s+(?:19|20)\d{2}\b",
    re.IGNORECASE,
)

YEAR_ONLY = re.compile(r"\b(?:19|20)\d{2}\b")

def dedupe_inline_citations(text: str) -> str:
    """
    Collapses patterns like: [1][2][3] -> [1]
    and [1] [2] [3] -> [1]
    """
    # collapse adjacent citation chains
    text = re.sub(r"(\[\d+\])(?:\s*\[\d+\])+", r"\1", text)
    return text

def mask_unverified_dates(answer: str, context: str) -> str:
    """
    If answer contains date strings that don't appear in the retrieved context,
    replace them with '[date not verified in excerpts]'.
    """
    ctx = context.lower()

    # Mask full month-day-year dates not present in context
    for m in set(MONTH_DATE.findall(answer)):
        if m.lower() not in ctx:
            answer = answer.replace(m, "[date not verified in excerpts]")

    # Mask standalone years that don't appear in context (conservative)
    for y in set(YEAR_ONLY.findall(answer)):
        if y.lower() not in ctx:
            answer = re.sub(rf"\b{re.escape(y)}\b", "[year not verified in excerpts]", answer)

    return answer
