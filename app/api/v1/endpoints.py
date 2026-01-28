import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_llm_engine
from app.schemas import LessonRequest, Presentation
from app.services import LLMEngine, LLMGenerationError, LLMValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/slide",
    response_model=Presentation,
    status_code=status.HTTP_200_OK,
    summary="Generate complete presentation",
    description=(
        "Generates a complete lesson presentation with all slides at once. "
        "Returns a structured JSON response containing: title slide, agenda slide, "
        "content slides (as specified by n_slides), and conclusion slide."
    ),
    response_description="Complete presentation with all slides structured as JSON",
    tags=["Presentations"],
)
async def generate_slides(
    request: LessonRequest,
    engine: LLMEngine = Depends(get_llm_engine),
) -> Presentation:
    """
    Generate complete presentation synchronously.

    This endpoint processes the request with an LLM and returns the complete
    structured presentation containing all slides.
    """
    try:
        presentation = await engine.generate_presentation(request)
        return presentation
    except LLMValidationError as e:
        logger.error(f"Validation error generating slides: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Generated content doesn't match expected schema: {str(e)}",
        ) from e
    except LLMGenerationError as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error generating slides: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/streaming",
    summary="Stream presentation slide by slide",
    description=(
        "Generates and streams the presentation slide by slide using Server-Sent Events (SSE). "
        "The client receives each slide as it is generated, allowing for progressive rendering. "
        "Each SSE event contains a complete, validated Slide object. "
        "Use this endpoint when you want to show slides to users as they become available."
    ),
    response_description="Server-Sent Events stream with individual slides",
    tags=["Presentations"],
)
async def generate_slides_stream(
    request: LessonRequest,
    engine: LLMEngine = Depends(get_llm_engine),
):
    """
    Stream presentation generation via Server-Sent Events (SSE).

    This endpoint generates and streams slides one by one as they are created.
    Each SSE event contains a complete Slide object (title, agenda, content, or conclusion).

    Event format:
    - data: {slide JSON} - For each generated slide
    - event: done, data: [DONE] - When generation is complete
    - event: error, data: {error JSON} - If an error occurs
    """

    async def sse_generator() -> AsyncGenerator[str, None]:
        slide_count = 0
        try:
            async for slide in engine.stream_presentation(request):
                slide_count += 1
                data = json.dumps(slide.model_dump(), ensure_ascii=False)
                yield f"data: {data}\n\n"

            yield "event: done\ndata: [DONE]\n\n"
            logger.info(f"Successfully streamed {slide_count} slides")

        except LLMValidationError as e:
            logger.error(f"Validation error in stream: {e}")
            error_data = json.dumps(
                {"error": "Validation error", "detail": str(e)}, ensure_ascii=False
            )
            yield f"event: error\ndata: {error_data}\n\n"
        except LLMGenerationError as e:
            logger.error(f"Generation error in stream: {e}")
            error_data = json.dumps(
                {"error": "Generation error", "detail": str(e)}, ensure_ascii=False
            )
            yield f"event: error\ndata: {error_data}\n\n"
        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
            error_data = json.dumps(
                {"error": "Unexpected error", "detail": str(e)}, ensure_ascii=False
            )
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        },
    )
