"""Aggregate-only product analytics. Never pass message content or labels here."""

import hashlib
import hmac
from typing import Any

from ..config import settings


def user_hash(user_id: str) -> str:
    if not settings.analytics_salt:
        raise RuntimeError("Analytics salt is not configured")
    return hmac.new(settings.analytics_salt.encode(), user_id.encode(), hashlib.sha256).hexdigest()


def track(user_id: str, event: str, **properties: Any) -> None:
    if not settings.posthog_api_key:
        return
    from posthog import Posthog

    Posthog(settings.posthog_api_key, host=settings.posthog_host).capture(
        distinct_id=user_hash(user_id), event=event, properties=properties
    )


def session_started(user_id: str, mode: str, session_index: int) -> None:
    track(user_id, "session_started", mode=mode, thread_session_index=int(session_index))


def session_ended(user_id: str, mode: str, duration_sec: float, end_reason: str) -> None:
    track(user_id, "session_ended", mode=mode, duration_sec=int(duration_sec), end_reason=end_reason)


def mood_checkin(user_id: str, mood_score: int) -> None:
    if mood_score not in range(1, 6):
        raise ValueError("mood_score must be between 1 and 5")
    track(user_id, "mood_checkin", score=mood_score)


def repeat_checkin_shown(user_id: str, threshold: int) -> None:
    if threshold not in (3, 6):
        raise ValueError("repeat-use threshold must be 3 or 6")
    track(user_id, "repeat_use_checkin_shown", threshold=threshold)


def grief_redirect_served(user_id: str) -> None:
    track(user_id, "grief_redirect_served")


def crisis_redirect_served(user_id: str) -> None:
    track(user_id, "crisis_redirect_served")


def thread_deleted(user_id: str, days_since_import: int, session_count: int) -> None:
    track(user_id, "thread_deleted", days_since_import=days_since_import, session_count=session_count)