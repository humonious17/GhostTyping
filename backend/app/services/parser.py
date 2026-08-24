"""PRD 5.1 — parse pasted/exported threads into structured messages,
strip PII that isn't needed for style modeling."""
import re

PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

def strip_pii(text: str) -> str:
    text = PHONE.sub("[number]", text)
    text = EMAIL.sub("[email]", text)
    return text

def parse_pasted(raw: str) -> list[dict]:
    """
    Accepts lines like:
        Name: message text
    or alternating blocks. Returns [{"speaker": "a"|"b", "text": str}, ...]
    """
    messages = []
    speakers_seen = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        who, _, text = line.partition(":")
        who, text = who.strip(), strip_pii(text.strip())
        if who not in speakers_seen:
            speakers_seen.append(who)
        speaker = "other" if who == speakers_seen[0] else "user"
        messages.append({"speaker": speaker, "text": text})
    return messages
