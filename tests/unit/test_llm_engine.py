from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas import LessonRequest, Presentation
from app.services.llm_engine import (
    LLMEngine,
    LLMEngineError,
    LLMGenerationError,
    LLMValidationError,
)


class TestExceptions:
    """Tests for custom exceptions."""

    def test_llm_engine_error_is_exception(self):
        """Test that LLMEngineError is an Exception."""
        assert issubclass(LLMEngineError, Exception)

    def test_llm_generation_error_is_engine_error(self):
        """Test that LLMGenerationError inherits from LLMEngineError."""
        assert issubclass(LLMGenerationError, LLMEngineError)

    def test_llm_validation_error_is_engine_error(self):
        """Test that LLMValidationError inherits from LLMEngineError."""
        assert issubclass(LLMValidationError, LLMEngineError)

    def test_exception_message(self):
        """Test that exceptions preserve message."""
        error = LLMGenerationError("Test error message")
        assert str(error) == "Test error message"


class TestLLMEngineInit:
    """Tests for LLMEngine initialization."""

    @patch("app.services.llm_engine.settings")
    @patch("app.services.llm_engine.ChatGoogleGenerativeAI")
    def test_init_with_google_provider(self, mock_gemini, mock_settings):
        """Test initialization with Google provider."""
        mock_settings.get_llm_provider.return_value = "google"
        mock_settings.GOOGLE_API_KEY = "test-key"
        mock_settings.DEFAULT_TEMPERATURE = 0.5
        mock_settings.DEFAULT_TIMEOUT = None
        mock_settings.DEFAULT_MAX_RETRIES = 2

        engine = LLMEngine(provider="google")

        assert engine.provider == "google"
        assert engine.model == "gemini-2.0-flash"
        mock_gemini.assert_called_once()

    @patch("app.services.llm_engine.settings")
    @patch("app.services.llm_engine.ChatOpenAI")
    def test_init_with_openai_provider(self, mock_openai, mock_settings):
        """Test initialization with OpenAI provider."""
        mock_settings.get_llm_provider.return_value = "openai"
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.DEFAULT_TEMPERATURE = 0.5
        mock_settings.DEFAULT_TIMEOUT = None
        mock_settings.DEFAULT_MAX_RETRIES = 2

        engine = LLMEngine(provider="openai")

        assert engine.provider == "openai"
        assert engine.model == "gpt-4"
        mock_openai.assert_called_once()

    @patch("app.services.llm_engine.settings")
    def test_init_with_unsupported_provider(self, mock_settings):
        """Test initialization with unsupported provider raises error."""
        mock_settings.get_llm_provider.return_value = "unsupported"
        mock_settings.DEFAULT_TEMPERATURE = 0.5

        with pytest.raises(ValueError) as exc_info:
            LLMEngine(provider="unsupported")

        assert "unsupported" in str(exc_info.value).lower()

    @patch("app.services.llm_engine.settings")
    def test_init_without_api_key_raises_error(self, mock_settings):
        """Test initialization without API key raises error."""
        mock_settings.get_llm_provider.return_value = "google"
        mock_settings.GOOGLE_API_KEY = None
        mock_settings.DEFAULT_TEMPERATURE = 0.5

        with pytest.raises(ValueError) as exc_info:
            LLMEngine(provider="google")

        assert "api_key" in str(exc_info.value).lower()

    @patch("app.services.llm_engine.settings")
    @patch("app.services.llm_engine.ChatGoogleGenerativeAI")
    def test_init_with_custom_temperature(self, mock_gemini, mock_settings):
        """Test initialization with custom temperature."""
        mock_settings.get_llm_provider.return_value = "google"
        mock_settings.GOOGLE_API_KEY = "test-key"
        mock_settings.DEFAULT_TEMPERATURE = 0.5
        mock_settings.DEFAULT_TIMEOUT = None
        mock_settings.DEFAULT_MAX_RETRIES = 2

        engine = LLMEngine(provider="google", temperature=0.8)

        assert engine.temperature == 0.8

    @patch("app.services.llm_engine.settings")
    @patch("app.services.llm_engine.ChatGoogleGenerativeAI")
    def test_init_with_custom_model(self, mock_gemini, mock_settings):
        """Test initialization with custom model."""
        mock_settings.get_llm_provider.return_value = "google"
        mock_settings.GOOGLE_API_KEY = "test-key"
        mock_settings.DEFAULT_TEMPERATURE = 0.5
        mock_settings.DEFAULT_TIMEOUT = None
        mock_settings.DEFAULT_MAX_RETRIES = 2

        engine = LLMEngine(provider="google", model="gemini-pro")

        assert engine.model == "gemini-pro"


class TestDefaultModel:
    """Tests for default model selection."""

    @patch("app.services.llm_engine.settings")
    @patch("app.services.llm_engine.ChatGoogleGenerativeAI")
    def test_google_default_model(self, mock_gemini, mock_settings):
        """Test default model for Google provider."""
        mock_settings.get_llm_provider.return_value = "google"
        mock_settings.GOOGLE_API_KEY = "test-key"
        mock_settings.DEFAULT_TEMPERATURE = 0.5
        mock_settings.DEFAULT_TIMEOUT = None
        mock_settings.DEFAULT_MAX_RETRIES = 2

        engine = LLMEngine(provider="google")

        assert engine.model == "gemini-2.0-flash"

    @patch("app.services.llm_engine.settings")
    @patch("app.services.llm_engine.ChatOpenAI")
    def test_openai_default_model(self, mock_openai, mock_settings):
        """Test default model for OpenAI provider."""
        mock_settings.get_llm_provider.return_value = "openai"
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.DEFAULT_TEMPERATURE = 0.5
        mock_settings.DEFAULT_TIMEOUT = None
        mock_settings.DEFAULT_MAX_RETRIES = 2

        engine = LLMEngine(provider="openai")

        assert engine.model == "gpt-4"


class TestGeneratePresentation:
    """Tests for presentation generation."""

    @pytest.fixture
    def mock_engine(self, sample_presentation: Presentation):
        """Create a mocked LLMEngine."""
        with patch("app.services.llm_engine.settings") as mock_settings, patch(
            "app.services.llm_engine.ChatGoogleGenerativeAI"
        ) as mock_gemini:
            mock_settings.get_llm_provider.return_value = "google"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.DEFAULT_TEMPERATURE = 0.5
            mock_settings.DEFAULT_TIMEOUT = None
            mock_settings.DEFAULT_MAX_RETRIES = 2

            # Mock the LLM chain
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(return_value=sample_presentation)

            mock_llm_instance = MagicMock()
            mock_llm_instance.with_structured_output.return_value = mock_llm_instance
            mock_llm_instance.__or__ = MagicMock(return_value=mock_chain)

            mock_gemini.return_value = mock_llm_instance

            engine = LLMEngine(provider="google")
            engine._build_chain = MagicMock(return_value=mock_chain)

            yield engine

    @pytest.mark.asyncio
    async def test_generate_presentation_success(
        self,
        mock_engine: LLMEngine,
        sample_presentation: Presentation,
    ):
        """Test successful presentation generation."""
        request = LessonRequest(
            topic="Photosynthesis",
            grade="7th grade",
            n_slides=3,
        )

        result = await mock_engine.generate_presentation(request)

        assert isinstance(result, Presentation)
        assert result.topic == sample_presentation.topic

    @pytest.mark.asyncio
    async def test_generate_presentation_calls_build_chain(
        self,
        mock_engine: LLMEngine,
    ):
        """Test that generate_presentation calls _build_chain."""
        request = LessonRequest(
            topic="Math",
            grade="5th grade",
            n_slides=2,
        )

        await mock_engine.generate_presentation(request)

        mock_engine._build_chain.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_generate_presentation_invalid_result_type(self):
        """Test that invalid result type raises LLMGenerationError with validation message."""
        with patch("app.services.llm_engine.settings") as mock_settings, patch(
            "app.services.llm_engine.ChatGoogleGenerativeAI"
        ) as mock_gemini:
            mock_settings.get_llm_provider.return_value = "google"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.DEFAULT_TEMPERATURE = 0.5
            mock_settings.DEFAULT_TIMEOUT = None
            mock_settings.DEFAULT_MAX_RETRIES = 2

            # Mock chain to return wrong type
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(return_value={"wrong": "type"})

            mock_llm_instance = MagicMock()
            mock_gemini.return_value = mock_llm_instance

            engine = LLMEngine(provider="google")
            engine._build_chain = MagicMock(return_value=mock_chain)

            request = LessonRequest(
                topic="Math",
                grade="5th grade",
                n_slides=2,
            )

            with pytest.raises(LLMGenerationError) as exc_info:
                await engine.generate_presentation(request)

            assert "unexpected type" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_presentation_llm_error(self):
        """Test that LLM errors are wrapped in LLMGenerationError."""
        with patch("app.services.llm_engine.settings") as mock_settings, patch(
            "app.services.llm_engine.ChatGoogleGenerativeAI"
        ) as mock_gemini:
            mock_settings.get_llm_provider.return_value = "google"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.DEFAULT_TEMPERATURE = 0.5
            mock_settings.DEFAULT_TIMEOUT = None
            mock_settings.DEFAULT_MAX_RETRIES = 2

            # Mock chain to raise error
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(side_effect=Exception("API Error"))

            mock_llm_instance = MagicMock()
            mock_gemini.return_value = mock_llm_instance

            engine = LLMEngine(provider="google")
            engine._build_chain = MagicMock(return_value=mock_chain)

            request = LessonRequest(
                topic="Math",
                grade="5th grade",
                n_slides=2,
            )

            with pytest.raises(LLMGenerationError) as exc_info:
                await engine.generate_presentation(request)

            assert "failed to generate" in str(exc_info.value).lower()


class TestStreamPresentation:
    """Tests for presentation streaming."""

    @pytest.mark.asyncio
    async def test_stream_presentation_yields_presentations(
        self,
        sample_presentation: Presentation,
    ):
        """Test that stream_presentation yields Presentation objects."""
        with patch("app.services.llm_engine.settings") as mock_settings, patch(
            "app.services.llm_engine.ChatGoogleGenerativeAI"
        ) as mock_gemini:
            mock_settings.get_llm_provider.return_value = "google"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.DEFAULT_TEMPERATURE = 0.5
            mock_settings.DEFAULT_TIMEOUT = None
            mock_settings.DEFAULT_MAX_RETRIES = 2

            # Mock async generator
            async def mock_astream(_):
                yield sample_presentation

            mock_chain = MagicMock()
            mock_chain.astream = mock_astream

            mock_llm_instance = MagicMock()
            mock_gemini.return_value = mock_llm_instance

            engine = LLMEngine(provider="google")
            engine._build_chain = MagicMock(return_value=mock_chain)

            request = LessonRequest(
                topic="Math",
                grade="5th grade",
                n_slides=2,
            )

            results = []
            async for chunk in engine.stream_presentation(request):
                results.append(chunk)

            assert len(results) == 1
            assert isinstance(results[0], Presentation)

    @pytest.mark.asyncio
    async def test_stream_presentation_error(self):
        """Test that streaming errors are wrapped in LLMGenerationError."""
        with patch("app.services.llm_engine.settings") as mock_settings, patch(
            "app.services.llm_engine.ChatGoogleGenerativeAI"
        ) as mock_gemini:
            mock_settings.get_llm_provider.return_value = "google"
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.DEFAULT_TEMPERATURE = 0.5
            mock_settings.DEFAULT_TIMEOUT = None
            mock_settings.DEFAULT_MAX_RETRIES = 2

            # Mock async generator that raises error
            async def mock_astream(_):
                raise Exception("Stream error")
                yield  # Make it a generator

            mock_chain = MagicMock()
            mock_chain.astream = mock_astream

            mock_llm_instance = MagicMock()
            mock_gemini.return_value = mock_llm_instance

            engine = LLMEngine(provider="google")
            engine._build_chain = MagicMock(return_value=mock_chain)

            request = LessonRequest(
                topic="Math",
                grade="5th grade",
                n_slides=2,
            )

            with pytest.raises(LLMGenerationError) as exc_info:
                async for _ in engine.stream_presentation(request):
                    pass

            assert "failed to stream" in str(exc_info.value).lower()
