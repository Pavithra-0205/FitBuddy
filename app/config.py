from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitBuddy"
    database_url: str = "sqlite:///./fitbuddy.db"
    gemini_api_key: str | None = None
    gemini_workout_model: str = "gemini-3.8-flash"
    gemini_nutrition_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: int = 60
    admin_token: str | None = None
    allow_ai_fallback: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
