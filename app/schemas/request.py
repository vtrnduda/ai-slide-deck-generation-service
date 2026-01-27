from pydantic import BaseModel, Field, field_validator, model_validator


class LessonRequest(BaseModel):
    """
    Request model for slide deck generation.

    Represents the input parameters required to generate a lesson presentation.
    The presentation will include: 1 title slide, 1 agenda slide, n_slides content slides,
    and 1 conclusion slide (total = n_slides + 3).
    """

    topic: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The main subject of the lesson (e.g., 'French Revolution', 'Photosynthesis')",
        examples=["French Revolution", "Photosynthesis", "Introduction to Algebra"],
    )

    grade: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="The students' grade level or educational stage (e.g., '7th grade', 'High School')",
        examples=["7th grade", "High School", "Elementary School"],
    )

    context: str = Field(
        default="",
        max_length=2000,
        description=(
            "Additional context provided by the teacher. "
            "Can include learning objectives, specific focus areas, or any relevant details. "
            "Limited to 2000 characters for cost control."
        ),
        examples=["Focus on the economic causes and social impact"],
    )

    n_slides: int = Field(
        ...,
        ge=1,
        le=15,
        description=(
            "Number of content slides to generate. "
            "Note: This excludes the title, agenda, and conclusion slides. "
            "Total slides returned will be n_slides + 3."
        ),
        examples=[5, 10],
    )

    @field_validator("topic")
    @classmethod
    def validate_and_sanitize_topic(cls, v: str) -> str:
        """Sanitize topic by stripping whitespace and validating it's not empty after trimming."""
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Topic cannot be empty or only whitespace")
        return sanitized

    @field_validator("grade")
    @classmethod
    def validate_and_sanitize_grade(cls, v: str) -> str:
        """Sanitize grade by stripping whitespace and validating it's not empty after trimming."""
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Grade cannot be empty or only whitespace")
        return sanitized

    @field_validator("context")
    @classmethod
    def sanitize_context(cls, v: str) -> str:
        """Sanitize context by stripping leading/trailing whitespace."""
        return v.strip()

    @model_validator(mode="after")
    def validate_request(self) -> "LessonRequest":
        """Additional cross-field validations if needed."""
        return self  # TODO: Add validations like checking if topic + context don't exceed certain limits
