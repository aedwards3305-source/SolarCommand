"""Application configuration loaded from environment variables."""

import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings

_DEFAULT_JWT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    app_name: str = "SolarCommand"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://solar:solar@localhost:5432/solarcommand"
    database_url_sync: str = "postgresql://solar:solar@localhost:5432/solarcommand"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "solar@example.com"

    # AI Provider — Anthropic Claude (primary)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    ai_temperature: float = 0.2
    ai_max_tokens: int = 800
    ai_prompt_version: str = "v1"
    ai_allow_auto_actions: bool = False  # Must stay false in production
    ai_cost_tracking: bool = True

    # Voice provider
    voice_provider: str = "twilio"  # twilio, vapi, retell
    voice_call_cost_usd: float = 0.80  # Cost per outbound voice call
    vapi_api_key: str = ""
    vapi_phone_number_id: str = ""
    vapi_model: str = "claude-sonnet-4-5-20250929"  # model for Vapi AI assistant
    retell_api_key: str = ""

    # Enrichment providers
    pdl_api_key: str = ""  # People Data Labs
    melissa_api_key: str = ""  # Melissa Data
    tracerfy_api_key: str = ""  # Tracerfy skip tracing
    enrichment_confidence_min: float = 0.5  # minimum confidence to accept enrichment

    # Legacy OpenAI fallback (optional)
    openai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_base_url: str = "https://api.openai.com/v1"

    # SMS auto-reply mode: False = suggest-only, True = auto-send
    sms_auto_reply_enabled: bool = False

    # Webhook signature verification
    twilio_webhook_secret: str = ""

    # Webhook API key — shared secret for non-Twilio webhook endpoints
    webhook_api_key: str = ""

    # Rate limiting (requests per minute for webhooks)
    webhook_rate_limit: int = 60

    # CORS — comma-separated allowed origins
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # JWT Auth
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours

    # Scoring
    score_hot_threshold: int = 75
    score_warm_threshold: int = 50

    # Outreach windows (Eastern Time)
    call_start_hour: int = 9
    call_end_hour: int = 20
    sms_start_hour: int = 9
    sms_end_hour: int = 21

    model_config = {"env_file": (".env", "../.env"), "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    if settings.jwt_secret == _DEFAULT_JWT_SECRET and not settings.debug:
        warnings.warn(
            "JWT_SECRET is using the default value! Set a secure random secret "
            "via JWT_SECRET env var before deploying to production.",
            stacklevel=2,
        )

    return settings
