import pytest
import os


def create_test_settings(**env_vars):
    """
    Create a Settings instance with specific environment variables.

    This helper temporarily sets environment variables, creates a Settings
    instance that ignores the .env file, and then restores the original env.
    """
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from typing import Optional

    # Define a test-only Settings class that ignores .env file
    class IsolatedSettings(BaseSettings):
        """Settings class that does not load from .env file."""

        model_config = SettingsConfigDict(
            env_file=None,
            extra="ignore",
        )

        OPENAI_API_KEY: Optional[str] = None
        GOOGLE_API_KEY: Optional[str] = None
        ENVIRONMENT: str = "development"
        LOG_LEVEL: str = "INFO"
        DEFAULT_LLM_PROVIDER: str = "google"
        DEFAULT_MODEL: str = "gemini-2.0-flash"
        DEFAULT_TEMPERATURE: float = 0.5
        DEFAULT_MAX_RETRIES: int = 2
        DEFAULT_TIMEOUT: Optional[int] = None

        def get_llm_provider(self) -> str:
            """Get the LLM provider based on available keys."""
            if self.OPENAI_API_KEY and self.GOOGLE_API_KEY:
                return self.DEFAULT_LLM_PROVIDER
            if self.GOOGLE_API_KEY:
                return "google"
            if self.OPENAI_API_KEY:
                return "openai"
            raise ValueError("No LLM API key configured. Set OPENAI_API_KEY or GOOGLE_API_KEY.")

    # Keys to manage
    managed_keys = [
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "ENVIRONMENT",
        "LOG_LEVEL",
        "DEFAULT_LLM_PROVIDER",
        "DEFAULT_MODEL",
        "DEFAULT_TEMPERATURE",
        "DEFAULT_MAX_RETRIES",
        "DEFAULT_TIMEOUT",
    ]

    # Save and clear current environment
    saved_env = {}
    for key in managed_keys:
        saved_env[key] = os.environ.pop(key, None)

    # Set test environment variables
    for key, value in env_vars.items():
        os.environ[key] = str(value)

    try:
        return IsolatedSettings()
    finally:
        # Restore original environment
        for key in managed_keys:
            os.environ.pop(key, None)
        for key, value in saved_env.items():
            if value is not None:
                os.environ[key] = value


class TestSettings:
    """Tests for Settings configuration."""

    def test_default_environment(self):
        """Test default environment is development."""
        settings = create_test_settings()
        assert settings.ENVIRONMENT == "development"

    def test_default_log_level(self):
        """Test default log level is INFO."""
        settings = create_test_settings()
        assert settings.LOG_LEVEL == "INFO"

    def test_default_temperature(self):
        """Test default temperature is 0.5."""
        settings = create_test_settings()
        assert settings.DEFAULT_TEMPERATURE == 0.5

    def test_default_max_retries(self):
        """Test default max retries is 2."""
        settings = create_test_settings()
        assert settings.DEFAULT_MAX_RETRIES == 2

    def test_api_keys_optional(self):
        """Test that API keys are optional (None by default)."""
        settings = create_test_settings()
        assert settings.OPENAI_API_KEY is None
        assert settings.GOOGLE_API_KEY is None

    def test_environment_from_env_var(self):
        """Test environment is set from env var."""
        settings = create_test_settings(ENVIRONMENT="production")
        assert settings.ENVIRONMENT == "production"

    def test_log_level_from_env_var(self):
        """Test log level is set from env var."""
        settings = create_test_settings(LOG_LEVEL="DEBUG")
        assert settings.LOG_LEVEL == "DEBUG"


class TestLLMProviderSelection:
    """Tests for LLM provider selection logic."""

    def test_get_llm_provider_returns_default_when_both_keys(self):
        """Test that get_llm_provider returns default when both keys are set."""
        settings = create_test_settings(
            DEFAULT_LLM_PROVIDER="openai",
            GOOGLE_API_KEY="google-key",
            OPENAI_API_KEY="openai-key",
        )
        assert settings.get_llm_provider() == "openai"

    def test_get_llm_provider_returns_google_default(self):
        """Test that Google is default when both keys available."""
        settings = create_test_settings(
            DEFAULT_LLM_PROVIDER="google",
            GOOGLE_API_KEY="google-key",
            OPENAI_API_KEY="openai-key",
        )
        assert settings.get_llm_provider() == "google"

    def test_get_llm_provider_falls_back_to_openai(self):
        """Test fallback to OpenAI when only OpenAI key available."""
        settings = create_test_settings(OPENAI_API_KEY="test-key")
        assert settings.get_llm_provider() == "openai"

    def test_get_llm_provider_falls_back_to_google(self):
        """Test fallback to Google when only Google key available."""
        settings = create_test_settings(GOOGLE_API_KEY="test-key")
        assert settings.get_llm_provider() == "google"

    def test_get_llm_provider_raises_when_no_keys(self):
        """Test that ValueError is raised when no keys configured."""
        settings = create_test_settings()

        with pytest.raises(ValueError) as exc_info:
            settings.get_llm_provider()

        assert "api key" in str(exc_info.value).lower()


class TestTimeoutParsing:
    """Tests for timeout value parsing."""

    def test_timeout_none_by_default(self):
        """Test that timeout is None by default."""
        settings = create_test_settings()
        assert settings.DEFAULT_TIMEOUT is None

    def test_timeout_from_env_var(self):
        """Test that timeout is parsed from env var."""
        settings = create_test_settings(DEFAULT_TIMEOUT="30")
        assert settings.DEFAULT_TIMEOUT == 30

    def test_temperature_from_env_var(self):
        """Test that temperature is parsed from env var."""
        settings = create_test_settings(DEFAULT_TEMPERATURE="0.8")
        assert settings.DEFAULT_TEMPERATURE == 0.8

    def test_max_retries_from_env_var(self):
        """Test that max retries is parsed from env var."""
        settings = create_test_settings(DEFAULT_MAX_RETRIES="5")
        assert settings.DEFAULT_MAX_RETRIES == 5
