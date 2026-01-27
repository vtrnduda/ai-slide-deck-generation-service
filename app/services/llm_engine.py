import logging
from collections.abc import AsyncGenerator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr, ValidationError

from app.core.config import settings
from app.schemas import LessonRequest, Presentation
from app.services.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class LLMEngineError(Exception):
    """Base exception for LLM engine errors."""

    pass


class LLMGenerationError(LLMEngineError):
    """Raised when LLM generation fails."""

    pass


class LLMValidationError(LLMEngineError):
    """Raised when LLM output fails Pydantic validation."""

    pass


class LLMEngine:
    """
    Engine for generating lesson presentations using LangChain and LLMs.

    Supports both OpenAI and Google Gemini providers with structured output
    generation using Pydantic models.
    """

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ):
        """
        Initialize the LLM engine.

        Args:
            provider: LLM provider ("openai" or "google"). If None, uses settings default.
            model: Model name. If None, uses provider default.
            temperature: Sampling temperature. If None, uses settings default.
        """
        self.provider = provider or settings.get_llm_provider()
        self.model = model or self._get_default_model()
        self.temperature = temperature or settings.DEFAULT_TEMPERATURE

        self.llm = self._initialize_llm()
        self._chain: Runnable | None = None

    def _get_default_model(self) -> str:
        """Get default model for the selected provider."""
        if self.provider == "openai":
            return "gpt-4"
        return "gemini-2.0-flash"

    def _initialize_llm(self) -> ChatOpenAI | ChatGoogleGenerativeAI:
        """
        Initialize the LLM instance based on provider.

        Returns:
            Configured LLM instance.

        Raises:
            ValueError: If provider is not supported or API key is missing.
        """
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                api_key=SecretStr(settings.OPENAI_API_KEY),
                timeout=settings.DEFAULT_TIMEOUT,
                max_retries=settings.DEFAULT_MAX_RETRIES,
            )

        if self.provider == "google":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for Google provider")
            return ChatGoogleGenerativeAI(
                model=self.model,
                temperature=self.temperature,
                google_api_key=settings.GOOGLE_API_KEY,
                timeout=settings.DEFAULT_TIMEOUT,
                max_retries=settings.DEFAULT_MAX_RETRIES,
            )

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _build_chain(self, request: LessonRequest) -> Runnable:
        """
        Build the LangChain chain for presentation generation.

        Args:
            request: Lesson request with all parameters.

        Returns:
            Configured LangChain Runnable chain.
        """
        # Format all prompts completely before creating ChatPromptTemplate
        system_prompt = SYSTEM_PROMPT.format(
            n_slides=request.n_slides,
            grade=request.grade,
            context=request.context or "No specific context provided.",
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            topic=request.topic,
            grade=request.grade,
            n_slides=request.n_slides,
            context=request.context or "No specific context provided.",
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )

        # Use structured output to ensure Pydantic validation
        structured_llm = self.llm.with_structured_output(Presentation)

        return prompt | structured_llm

    async def generate_presentation(self, request: LessonRequest) -> Presentation:
        """
        Generate a complete presentation synchronously.

        Args:
            request: Lesson request with topic, grade, context, and n_slides.

        Returns:
            Generated Presentation model.

        Raises:
            LLMGenerationError: If generation fails.
            LLMValidationError: If output doesn't match schema.
        """
        logger.info(
            f"Generating presentation (provider: {self.provider}, model: {self.model}) "
            f"for topic: {request.topic}, grade: {request.grade}, "
            f"n_slides: {request.n_slides}"
        )

        try:
            # Build chain with request-specific parameters
            chain = self._build_chain(request)

            # Invoke chain asynchronously
            result = await chain.ainvoke({})

            # Validate result is a Presentation instance
            if not isinstance(result, Presentation):
                raise LLMValidationError(
                    f"LLM returned unexpected type: {type(result)}. " f"Expected Presentation."
                )

            logger.info(f"Successfully generated presentation with {len(result.slides)} slides")
            return result

        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}")
            raise LLMValidationError(
                f"Generated content doesn't match Presentation schema: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Error generating presentation: {e}", exc_info=True)
            raise LLMGenerationError(f"Failed to generate presentation: {str(e)}") from e

    async def stream_presentation(
        self, request: LessonRequest
    ) -> AsyncGenerator[Presentation, None]:
        """
        Generate presentation slide by slide via streaming.

        Args:
            request: Lesson request with topic, grade, context, and n_slides.

        Yields:
            Partial Presentation models as slides are generated.

        Raises:
            LLMGenerationError: If generation fails.
            LLMValidationError: If output doesn't match schema.
        """
        logger.info(
            f"Streaming presentation generation (provider: {self.provider}) "
            f"for topic: {request.topic}"
        )

        try:
            chain = self._build_chain(request)

            # Stream results (no input needed, prompts are pre-formatted)
            async for chunk in chain.astream({}):
                if isinstance(chunk, Presentation):
                    logger.debug(f"Received chunk with {len(chunk.slides)} slides")
                    yield chunk
                elif hasattr(chunk, "slides"):
                    # Handle partial results if LLM supports it
                    try:
                        presentation = Presentation.model_validate(chunk)
                        yield presentation
                    except ValidationError as e:
                        logger.warning(f"Skipping invalid chunk: {e}")
                        continue

        except ValidationError as e:
            logger.error(f"Pydantic validation error during streaming: {e}")
            raise LLMValidationError(
                f"Streamed content doesn't match Presentation schema: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Error streaming presentation: {e}", exc_info=True)
            raise LLMGenerationError(f"Failed to stream presentation: {str(e)}") from e
