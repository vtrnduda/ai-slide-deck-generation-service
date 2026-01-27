"""
Slide model representing individual slides in a presentation.

Each slide has a type, title, and content, with optional fields
for images and interactive questions.
"""

from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import SlideType
from app.schemas.question import Question


class Slide(BaseModel):
    """
    Individual slide model representing a single slide in the presentation.

    Each slide has a type, title, and content. Optionally, it may include
    an image search query and/or a question for interactive learning.
    """

    type: SlideType = Field(
        ...,
        description="The structural type of the slide",
        examples=[SlideType.TITLE, SlideType.CONTENT],
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Clear and concise slide title",
        examples=["Introduction to Photosynthesis", "Key Concepts"],
    )

    content: str = Field(
        ...,
        min_length=1,
        description=(
            "The main text content of the slide. "
            "Can be formatted as bullet points, short paragraphs, or other structures "
            "appropriate for educational content."
        ),
        examples=["• First concept\n• Second concept\n• Third concept"],
    )

    image: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description=(
            "Optional search query for finding a relevant image. "
            "When present, this query can be used with an image provider to retrieve "
            "an image that aligns with the slide's content. "
            "Only included when an image would enhance the slide."
        ),
        examples=["photosynthesis diagram", "French Revolution painting"],
    )

    question: Question | None = Field(
        default=None,
        description=(
            "Optional multiple choice question for interactive learning. "
            "Should only appear in content slides, typically in the middle of the presentation. "
            "Must be relevant to the lesson context and content presented up to that point."
        ),
    )

    @model_validator(mode="after")
    def validate_slide_structure(self) -> "Slide":
        """
        Validate slide structure based on its type.

        - Title, agenda, and conclusion slides should not have questions
        - Only content slides can have questions
        """
        if self.type in (SlideType.TITLE, SlideType.AGENDA, SlideType.CONCLUSION):
            if self.question is not None:
                raise ValueError(
                    f"Questions can only be included in content slides, not in {self.type} slides"
                )

        return self
