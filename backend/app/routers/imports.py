"""PRD 5.1 — import flow. Paste-based for MVP; file/screenshot later.
Runs PII stripping, speaker parsing, style profile extraction,
and grief-context flagging (7.4) at import time."""

from backend.app.dependencies import require_onboarded
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..db import get_db
from ..models import Thread, User
from ..services.parser import parse_pasted
from ..services.style_profile import build_style_profile
from ..safety.grief_detector import flag_grief_context
from ..services.storage import configured_store

router = APIRouter(prefix="/threads")

class ImportThread(BaseModel):
    label: str            # user-chosen name for the simulated person ("M", "Sam's texts")
    raw_text: str         # pasted conversation

@router.post("")
def import_thread(body: ImportThread, db=Depends(get_db), user: User = Depends(require_onboarded)):
    messages = parse_pasted(body.raw_text)

    if len(messages) < 10:
        raise HTTPException(422, detail={
            "code": "too_few_messages",
            "message": "We need more of the conversation to work with (at least ~10 lines).",
        })

    other = [m for m in messages if m["speaker"] == "other"]
    joined = "\n".join(m["text"] for m in messages)
    grief_flagged = flag_grief_context(joined)

    thread = Thread(
        user_id=user.id,
        other_person_label=body.label.strip()[:40] or "them",
        parsed_messages=messages,
        # Profile built now; sessions check min threshold separately (5.1)
        style_profile=build_style_profile(other),
        grief_flagged=grief_flagged,
    )
    db.add(thread)
    db.flush()
    try:
        thread.raw_blob_key, thread.wrapped_dek = configured_store().put(
            user.id, thread.id, body.raw_text
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(503, detail={"code": "raw_storage_unavailable"}) from exc
    db.commit()
    db.refresh(thread)

    return {
        "thread_id": thread.id,
        "messages_parsed": len(messages),
        "style_reliable": len(other) >= 40,   # 5.1 minimum
        "grief_redirect_required": grief_flagged,  # 7.4 — frontend must show redirect UI
    }
