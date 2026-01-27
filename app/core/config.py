from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider API Keys
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # Application Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = "google"  # "openai" or "google"
    DEFAULT_MODEL: str = "gemini-1.5-flash"  # or "gpt-4" for OpenAI
    DEFAULT_TEMPERATURE: float = 0.5
    DEFAULT_MAX_RETRIES: int = 2
    DEFAULT_TIMEOUT: int | None = None

    @field_validator("DEFAULT_TIMEOUT", mode="before")
    @classmethod
    def parse_timeout(cls, v: str | int | None) -> int | None:
        """
        Parse timeout value from environment variable.

        Handles empty strings from .env file by converting them to None.
        """
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def get_llm_provider(self) -> str:
        """Get the configured LLM provider, with fallback logic."""
        if self.DEFAULT_LLM_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return "openai"
        if self.GOOGLE_API_KEY:
            return "google"
        raise ValueError("No LLM provider configured. Please set OPENAI_API_KEY or GOOGLE_API_KEY")


settings = Settings()
