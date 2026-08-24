import os
import socket
from pathlib import Path
from typing import Optional, List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_DIR = Path(__file__).resolve().parent
_API_DIR = _CONFIG_DIR.parent
_MONOREPO_ROOT = _API_DIR.parent.parent
_CWD = Path.cwd()

# Discover candidate .env files in priority order across CWD, api dir, and monorepo root
_CANDIDATE_PATHS = [
    _CWD / ".env.local",
    _CWD / ".env",
    _API_DIR / ".env.local",
    _API_DIR / ".env",
    _MONOREPO_ROOT / ".env.local",
    _MONOREPO_ROOT / ".env",
]

_SEEN = set()
_ENV_FILES: List[str] = []
for _p in _CANDIDATE_PATHS:
    try:
        _resolved = _p.resolve()
        if _resolved.is_file() and _resolved not in _SEEN:
            _SEEN.add(_resolved)
            _ENV_FILES.append(str(_resolved))
    except Exception:
        pass


class Settings(BaseSettings):
    # App General
    PROJECT_NAME: str = "Reading Game API"
    PORT: int = 8000
    DEBUG: bool = False

    # Provider Toggles
    LLM_PROVIDER: str = "vertex"
    STT_PROVIDER: str = "deepgram"
    TTS_PROVIDER: str = "cartesia"
    TELEPHONY_PROVIDER: str = "browser_only"

    # Databases & Queues
    REDIS_URL: str = "redis://localhost:6379/0"
    MONGO_URI: str = "mongodb://localhost:27018/reading_game_db"
    MONGO_DB_NAME: str = "reading_game_db"

    # LiveKit
    LIVEKIT_URL: Optional[str] = None
    NEXT_PUBLIC_LIVEKIT_URL: str = "ws://localhost:7880"
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: str = "secret"
    LIVEKIT_SIP_TRUNK_ID: Optional[str] = None

    # Third Party Keys
    DEEPGRAM_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"
    CARTESIA_API_KEY: Optional[str] = None

    # GCP
    GCP_PROJECT_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_LOCATION: str = "us-central1"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Telephony
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    EXOTEL_API_KEY: Optional[str] = None
    EXOTEL_API_TOKEN: Optional[str] = None
    EXOTEL_SUBDOMAIN: Optional[str] = None
    EXOTEL_EXOPHONE: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def sanitize_configuration(self):
        # Auto-fallback for Redis when running outside Docker host network
        if "://redis:" in self.REDIS_URL:
            try:
                socket.gethostbyname("redis")
            except Exception:
                self.REDIS_URL = self.REDIS_URL.replace("://redis:", "://localhost:")

        # Auto-fallback for MongoDB when running outside Docker host network
        if "://mongodb:" in self.MONGO_URI:
            try:
                socket.gethostbyname("mongodb")
            except Exception:
                self.MONGO_URI = self.MONGO_URI.replace("://mongodb:27017", "://localhost:27018")

        # Fix relative Google Application Credentials path if needed
        if self.GOOGLE_APPLICATION_CREDENTIALS:
            creds_path = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
            if not creds_path.is_absolute():
                for base in [_CWD, _API_DIR, _MONOREPO_ROOT]:
                    candidate = base / creds_path
                    if candidate.is_file():
                        self.GOOGLE_APPLICATION_CREDENTIALS = str(candidate.resolve())
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(candidate.resolve())
                        break
        return self


settings = Settings()
