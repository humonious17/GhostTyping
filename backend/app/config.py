from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://gt:gt@localhost:5432/ghosttyping"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"
    jwt_secret: str = "change-me-in-production"
    raw_imports_bucket: str = ""
    kms_key_id: str = ""
    posthog_api_key: str = ""
    posthog_host: str = "http://posthog:8000"
    analytics_salt: str = ""

    # PRD 5.1: minimum messages before style modeling is "reliable"
    min_messages_for_style: int = 40

    # PRD 7.2: time-boxing defaults (seconds)
    default_session_limit: int = 20 * 60

    # PRD 7.2: check-in thresholds on repeat use of same thread
    checkin_at_sessions: tuple[int, ...] = (3, 6)

    # PRD 7.7: auto-expiry of inactive threads
    retention_days: int = 365

    class Config:
        env_file = ".env"

settings = Settings()
