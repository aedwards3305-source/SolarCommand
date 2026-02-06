"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


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

    # OpenAI
    openai_api_key: str = ""

    # Scoring
    score_hot_threshold: int = 75
    score_warm_threshold: int = 50

    # Outreach windows (Eastern Time)
    call_start_hour: int = 9
    call_end_hour: int = 20
    sms_start_hour: int = 9
    sms_end_hour: int = 21

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
