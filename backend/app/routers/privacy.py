"""US-6 / 7.7 — verifiable cascading delete and data export.
Deletion is hard-delete, not soft-delete. A deletion token row is kept
(contains no content) so we can prove deletion happened if audited."""

from backend.app.dependencies import require_onboarded
from fastapi import APIRouter, HTTPException, Depends
from ..db import get_db
from ..models import Thread, Session as SessionRow, DeletionToken, User
from ..services.storage import configured_store

router = APIRouter(prefix="/privacy")

@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: str, db=Depends(get_db), user: User = Depends(require_onboarded)):
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(404)

    # privacy.py delete/export — verify ownership first
    if thread.user_id != user.id:
        raise HTTPException(404)   # 404, not 403 — don't leak existence of others' threads


    if thread.raw_blob_key:
        try:
            configured_store().delete(thread.raw_blob_key, thread.wrapped_dek)
        except RuntimeError as exc:
            db.rollback()
            raise HTTPException(503, detail={"code": "raw_storage_delete_failed"}) from exc

    # Cascading delete across every derived artifact (8.4 step 6)
    db.query(SessionRow).filter_by(thread_id=thread.id).delete(synchronize_session=False)

    token = DeletionToken(thread_id=thread.id)   # id-only tombstone record
    db.add(token)
    db.delete(thread)
    db.commit()

    return {"deleted": True, "deletion_receipt": token.id}

@router.get("/threads/{thread_id}/export")
def export_thread_data(thread_id: str, db=Depends(get_db), user: User = Depends(require_onboarded)):
    """GDPR-style access request for the importing user only."""
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(404)
    if thread.user_id != user.id:
        raise HTTPException(404)   # 404, not 403 — don't leak existence of others' threads

    sessions = db.query(SessionRow).filter_by(thread_id=thread_id).all()
    return {
        "thread_label": thread.other_person_label,
        "imported_message_count": len(thread.parsed_messages),
        "session_count": len(sessions),
        "sessions": [
            {"mode": s.mode, "started_at": s.started_at.isoformat(),
             "mood_checkin": s.mood_checkin}
            for s in sessions
        ],
        # Deliberately excludes verbatim simulated replies — see leak-vector note
        # from review: exports shouldn't be a channel for forwarding ghost text.
    }
