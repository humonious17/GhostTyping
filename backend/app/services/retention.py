"""Hard-expiry worker for inactive threads and their encrypted raw blobs."""

import datetime as dt

from sqlalchemy.orm import Session

from ..models import Session as SessionRow, Thread
from .storage import EncryptedStore


def expire_inactive_threads(db: Session, storage: EncryptedStore, retention_days: int, now: dt.datetime | None = None) -> int:
    cutoff = (now or dt.datetime.now(dt.timezone.utc)) - dt.timedelta(days=retention_days)
    expired = db.query(Thread).filter(Thread.last_active_at < cutoff).all()
    for thread in expired:
        if thread.raw_blob_key:
            storage.delete(thread.raw_blob_key, thread.wrapped_dek)
        db.query(SessionRow).filter_by(thread_id=thread.id).delete(synchronize_session=False)
        db.delete(thread)
    db.commit()
    return len(expired)