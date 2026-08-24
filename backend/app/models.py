import uuid, datetime as dt
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

def _uuid() -> str: return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    birthdate_confirmed_18_plus: Mapped[bool] = mapped_column(Boolean, default=False)  # 7.6
    onboarding_acknowledged_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

class Thread(Base):
    __tablename__ = "threads"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    other_person_label: Mapped[str] = mapped_column(String)  # user-chosen, not scraped
    raw_blob_key: Mapped[str | None] = mapped_column(String)  # object storage key
    wrapped_dek: Mapped[bytes | None] = mapped_column(LargeBinary)
    parsed_messages: Mapped[list] = mapped_column(JSON)
    style_profile: Mapped[dict | None] = mapped_column(JSON)
    grief_flagged: Mapped[bool] = mapped_column(Boolean, default=False)  # 7.4
    session_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    last_active_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

ImportedThread = Thread

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(ForeignKey("threads.id"))
    mode: Mapped[str] = mapped_column(String)  # unsaid | replay | question | goodbye | free
    transcript: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    end_reason: Mapped[str | None] = mapped_column(String)  # completed | timebox | user_exit | crisis_redirect
    mood_checkin: Mapped[int | None] = mapped_column(Integer)  # 1–5, post-session
    summary: Mapped[str | None] = mapped_column(Text)

class DeletionToken(Base):
    """PRD 6 / US-6: verifiable cascading delete."""
    __tablename__ = "deletions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(String)
    deleted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
