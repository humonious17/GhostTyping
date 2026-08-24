"""PRD 7.4 — detect likely deceased-person imports and redirect.
Deliberately conservative: false positives get a gentle redirect message,
false negatives are the dangerous case, so we over-match."""

GRIEF_PATTERNS = [
    r"\b(passed away|passed on|died|death|funeral|wake|burial|cremat\w+"
    r"|in memor(y|iam)|rest in peace|\brip\b|lost (him|her|them)|"
    r"since (he|she|they) (died|passed)|would have wanted)\b",
]

def flag_grief_context(thread_text: str) -> bool:
    import re
    lowered = thread_text.lower()
    return any(re.search(p, lowered) for p in GRIEF_PATTERNS)
