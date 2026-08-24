"""PRD 5.1 — extract a lightweight style profile via NLP stats.
No LLM call needed; cheap, auditable, easy to delete (7.7)."""

from collections import Counter
import re

def build_style_profile(messages: list[dict]) -> dict:
    texts = [m["text"] for m in messages]
    joined = " ".join(texts)
    words = re.findall(r"[a-z']+", joined.lower())
    lengths = [len(t.split()) for t in texts]
    emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", joined))

    return {
        "avg_msg_words": round(sum(lengths) / max(len(lengths), 1), 1),
        "punctuation_habits": {
            "exclamation_rate": round(joined.count("!") / max(len(texts), 1), 2),
            "question_rate": round(joined.count("?") / max(len(texts), 1), 2),
            "ellipsis_rate": round(joined.count("...") / max(len(texts), 1), 2),
        },
        "emoji_per_msg": round(emoji_count / max(len(texts), 1), 2),
        "top_phrases": [p for p, _ in Counter(
            " ".join(words[i:i+3]) for i in range(len(words) - 2)
        ).most_common(10)],
        "message_count": len(messages),
    }
