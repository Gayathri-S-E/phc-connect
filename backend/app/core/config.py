from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Smart Health & Supply Chain Resilience"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://app_user:local_dev_secret_password@localhost:5432/smarthealth_db",
        description="Async database connection string",
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5

    # JWT & Authentication
    JWT_SECRET: str = Field(
        default="local_dev_jwt_secret_key_must_be_overridden_in_production_environments_32_chars",
        description="Secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://phc-connect-1.onrender.com",
        "https://phc-connect.onrender.com",
    ]
    ALLOWED_ORIGIN_REGEX: str = r"https://.*\.onrender\.com"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*.onrender.com", "phc-connect.onrender.com", "phc-connect-1.onrender.com"]

    # Automatic monitoring (supply monitor + public-health analysis). Off by default so
    # tests and one-off scripts never start background work.
    ENABLE_BACKGROUND_JOBS: bool = False
    SUPPLY_MONITOR_INTERVAL_MINUTES: int = 60
    PUBLIC_HEALTH_ANALYSIS_INTERVAL_MINUTES: int = 24 * 60

    # Common AI Foundation (Google Gemini). The key lives only on the server; when it is empty the
    # assistants answer that the AI service is not configured instead of inventing replies.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # "auto" (default): Vertex AI with the Google service account when one is configured, else the API key.
    # "vertex" | "api_key" force one. Vertex needs no API key and bills through the GCP project.
    GEMINI_BACKEND: str = "auto"
    GEMINI_VERTEX_LOCATION: str = "global"
    GEMINI_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"
    AI_REQUEST_TIMEOUT_SECONDS: float = 30.0
    AI_MAX_MESSAGE_CHARS: int = 2000
    AI_HISTORY_MESSAGES: int = 12
    AI_MAX_TOOL_ROUNDS: int = 5
    AI_RATE_LIMIT_PER_MINUTE: int = 20
    AI_PENDING_ACTION_TTL_MINUTES: int = 15

    # Voice + multilingual (Google Cloud Speech-to-Text, Text-to-Speech, Translation; REST). The key lives only on the
    # server. With no key, or a feature toggled off, the voice endpoints answer 503 AI_NOT_CONFIGURED - never fake output.
    GOOGLE_CLOUD_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""  # optional; sent as x-goog-user-project (quota/billing project) when set
    GOOGLE_APPLICATION_CREDENTIALS: str = ""  # reserved for service-account auth; the REST client does not use it yet
    GOOGLE_STT_ENABLED: bool = True
    GOOGLE_TTS_ENABLED: bool = True
    GOOGLE_TRANSLATE_ENABLED: bool = True
    GOOGLE_STT_API_BASE: str = "https://speech.googleapis.com/v1"
    GOOGLE_TTS_API_BASE: str = "https://texttospeech.googleapis.com/v1"
    GOOGLE_TRANSLATE_API_BASE: str = "https://translation.googleapis.com/language/translate/v2"
    AI_VOICE_MAX_AUDIO_BASE64_CHARS: int = 1_048_576  # ~1 MB of base64 (~780 KB of audio, ~30-40 s of speech)
    AI_VOICE_MAX_TEXT_CHARS: int = 1500
    AI_VOICE_RATE_LIMIT_PER_MINUTE: int = 30

    # Google Maps Platform + BigQuery (app/integrations/google). All optional; unset -> 503 AI_NOT_CONFIGURED.
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""  # inline service-account JSON (alternative to GOOGLE_APPLICATION_CREDENTIALS path)
    BIGQUERY_DATASET: str = ""
    BIGQUERY_TABLE: str = "facility_daily_aggregates"
    BIGQUERY_LOCATION: str = "asia-south1"
    GOOGLE_MAPS_GEOCODE_BASE: str = "https://maps.googleapis.com/maps/api/geocode/json"
    GOOGLE_MAPS_ROUTES_BASE: str = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    GOOGLE_BIGQUERY_API_BASE: str = "https://bigquery.googleapis.com/bigquery/v2"
    GOOGLE_INTEGRATIONS_RATE_LIMIT_PER_MINUTE: int = 30
    GOOGLE_MAPS_REFINE_TOP_N: int = 5


settings = Settings()
