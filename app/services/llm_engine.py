import json
import logging
from collections.abc import AsyncGenerator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr, ValidationError

from app.core.config import settings
from app.schemas import LessonRequest, Presentation, Slide
from app.schemas.enums import SlideType
from app.services.prompts import (
    AGENDA_PLANNING_PROMPT,
    AGENDA_SLIDE_PROMPT,
    CONCLUSION_SLIDE_PROMPT,
    CONTENT_SLIDE_PROMPT,
    SLIDE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    TITLE_SLIDE_PROMPT,
    USER_PROMPT_TEMPLATE,
)

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
            return settings.FALLBACK_MODEL
        return settings.DEFAULT_MODEL

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

    async def _plan_agenda(self, request: LessonRequest) -> list[str]:
        """
        Plan the agenda/subtopics for the presentation.

        Args:
            request: Lesson request with topic, grade, context, and n_slides.

        Returns:
            List of subtopic strings for content slides.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an educational content planner. Return ONLY valid JSON.",
                ),
                (
                    "user",
                    AGENDA_PLANNING_PROMPT.format(
                        topic=request.topic,
                        grade=request.grade,
                        n_slides=request.n_slides,
                        context=request.context or "No specific context provided.",
                    ),
                ),
            ]
        )

        chain = prompt | self.llm
        result = await chain.ainvoke({})

        # Parse the JSON array from the response
        content = result.content if hasattr(result, "content") else str(result)

        # Clean up the response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        content = content.strip()

        try:
            subtopics = json.loads(content)
            if not isinstance(subtopics, list):
                raise ValueError("Expected a list of subtopics")
            return subtopics[: request.n_slides]  # Ensure correct count
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse agenda planning response: {e}")
            # Fallback: generate generic subtopics
            return [f"Topic {i + 1}" for i in range(request.n_slides)]

    async def _generate_single_slide(
        self,
        request: LessonRequest,
        slide_type: SlideType,
        **kwargs,
    ) -> Slide:
        """
        Generate a single slide of the specified type.

        Args:
            request: Lesson request with topic, grade, context.
            slide_type: Type of slide to generate.
            **kwargs: Additional parameters for specific slide types.

        Returns:
            Generated Slide object.
        """
        system_prompt = SLIDE_SYSTEM_PROMPT.format(
            grade=request.grade,
            context=request.context or "No specific context provided.",
        )

        if slide_type == SlideType.TITLE:
            user_prompt = TITLE_SLIDE_PROMPT.format(topic=request.topic)
        elif slide_type == SlideType.AGENDA:
            agenda_items = "\n".join(f"- {item}" for item in kwargs.get("subtopics", []))
            user_prompt = AGENDA_SLIDE_PROMPT.format(
                topic=request.topic,
                n_slides=request.n_slides,
                agenda_items=agenda_items,
            )
        elif slide_type == SlideType.CONTENT:
            slide_number = kwargs.get("slide_number", 1)
            total_slides = kwargs.get("total_content_slides", request.n_slides)
            subtopic = kwargs.get("subtopic", "")
            include_image = kwargs.get("include_image", False)
            include_question = kwargs.get("include_question", False)

            image_instruction = (
                '- Include an "image" field with a relevant search query for an image'
                if include_image
                else ""
            )
            question_instruction = (
                '- Include a "question" field with a multiple choice question '
                "(prompt, options array with 4 choices, and answer)"
                if include_question
                else ""
            )

            user_prompt = CONTENT_SLIDE_PROMPT.format(
                topic=request.topic,
                slide_number=slide_number,
                total_content_slides=total_slides,
                subtopic=subtopic,
                image_instruction=image_instruction,
                question_instruction=question_instruction,
            )
        elif slide_type == SlideType.CONCLUSION:
            covered_topics = "\n".join(f"- {item}" for item in kwargs.get("subtopics", []))
            user_prompt = CONCLUSION_SLIDE_PROMPT.format(
                topic=request.topic,
                covered_topics=covered_topics,
            )
        else:
            raise ValueError(f"Unknown slide type: {slide_type}")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )

        structured_llm = self.llm.with_structured_output(Slide)
        chain = prompt | structured_llm

        result = await chain.ainvoke({})

        if not isinstance(result, Slide):
            raise LLMValidationError(f"Expected Slide, got {type(result)}")

        # Ensure correct slide type
        if result.type != slide_type:
            result = Slide(
                type=slide_type,
                title=result.title,
                content=result.content,
                image=result.image,
                question=result.question,
            )

        return result

    async def stream_presentation(self, request: LessonRequest) -> AsyncGenerator[Slide, None]:
        """
        Generate presentation slide by slide via streaming.

        Each slide is generated individually and yielded as soon as it's ready,
        providing true streaming behavior.

        Args:
            request: Lesson request with topic, grade, context, and n_slides.

        Yields:
            Individual Slide objects as they are generated.

        Raises:
            LLMGenerationError: If generation fails.
            LLMValidationError: If output doesn't match schema.
        """
        logger.info(
            f"Streaming presentation generation (provider: {self.provider}) "
            f"for topic: {request.topic}, n_slides: {request.n_slides}"
        )

        try:
            # Step 1: Plan the agenda/subtopics
            logger.debug("Planning agenda subtopics...")
            subtopics = await self._plan_agenda(request)
            logger.debug(f"Planned subtopics: {subtopics}")

            # Step 2: Generate title slide
            logger.debug("Generating title slide...")
            title_slide = await self._generate_single_slide(request, SlideType.TITLE)
            yield title_slide
            logger.debug("Title slide generated and yielded")

            # Step 3: Generate agenda slide
            logger.debug("Generating agenda slide...")
            agenda_slide = await self._generate_single_slide(
                request,
                SlideType.AGENDA,
                subtopics=subtopics,
            )
            yield agenda_slide
            logger.debug("Agenda slide generated and yielded")

            # Step 4: Generate content slides one by one
            # Determine which slide gets the question (middle slide)
            question_slide_index = request.n_slides // 2

            for i, subtopic in enumerate(subtopics):
                logger.debug(f"Generating content slide {i + 1}/{request.n_slides}...")

                # Add image to some slides (every other slide)
                include_image = i % 2 == 0

                # Add question to the middle slide
                include_question = i == question_slide_index

                content_slide = await self._generate_single_slide(
                    request,
                    SlideType.CONTENT,
                    slide_number=i + 1,
                    total_content_slides=request.n_slides,
                    subtopic=subtopic,
                    include_image=include_image,
                    include_question=include_question,
                )
                yield content_slide
                logger.debug(f"Content slide {i + 1} generated and yielded")

            # Step 5: Generate conclusion slide
            logger.debug("Generating conclusion slide...")
            conclusion_slide = await self._generate_single_slide(
                request,
                SlideType.CONCLUSION,
                subtopics=subtopics,
            )
            yield conclusion_slide
            logger.debug("Conclusion slide generated and yielded")

            logger.info(
                f"Successfully streamed presentation with " f"{request.n_slides + 3} slides"
            )

        except ValidationError as e:
            logger.error(f"Pydantic validation error during streaming: {e}")
            raise LLMValidationError(f"Streamed content doesn't match Slide schema: {e}") from e
        except Exception as e:
            logger.error(f"Error streaming presentation: {e}", exc_info=True)
            raise LLMGenerationError(f"Failed to stream presentation: {str(e)}") from e
