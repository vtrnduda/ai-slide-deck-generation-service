"""
Presentation model representing a complete slide deck.

Contains all slides in the required structure and validates
the presentation follows the specified format.
"""


from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import SlideType
from app.schemas.slide import Slide


class Presentation(BaseModel):
    """
    Complete presentation model containing all slides.

    Represents the full slide deck structure with metadata about the lesson.
    The slides list must follow the required structure:
    - 1 title slide
    - 1 agenda slide
    - n content slides (where n = n_slides from request)
    - 1 conclusion slide
    """

    topic: str = Field(
        ...,
        description="The lesson topic (echoed from the request for context)",
        examples=["French Revolution"],
    )
    grade: str = Field(
        ...,
        description="The target student grade level (echoed from the request for context)",
        examples=["7th grade"],
    )
    slides: list[Slide] = Field(
        ...,
        min_length=3,
        description=(
            "Ordered list of slides. Must follow the structure: "
            "[title, agenda, ...content slides..., conclusion]"
        ),
    )

    @model_validator(mode="after")
    def validate_presentation_structure(self) -> "Presentation":
        """
        Validate that the presentation follows the required structure.

        Ensures:
        - First slide is title
        - Second slide is agenda
        - Last slide is conclusion
        - All middle slides are content slides
        - At least one content slide exists
        - Only one question exists (if any) and it's in a content slide
        """
        if not self.slides:
            raise ValueError("Presentation must contain at least one slide")

        # Validate first slide is title
        if self.slides[0].type != SlideType.TITLE:
            raise ValueError(
                f"First slide must be of type '{SlideType.TITLE}', "
                f"but got '{self.slides[0].type}'"
            )

        # Validate second slide is agenda
        if len(self.slides) < 2 or self.slides[1].type != SlideType.AGENDA:
            raise ValueError(
                f"Second slide must be of type '{SlideType.AGENDA}', "
                f"but got '{self.slides[1].type if len(self.slides) > 1 else 'none'}'"
            )

        # Validate last slide is conclusion
        if self.slides[-1].type != SlideType.CONCLUSION:
            raise ValueError(
                f"Last slide must be of type '{SlideType.CONCLUSION}', "
                f"but got '{self.slides[-1].type}'"
            )

        # Validate middle slides are all content slides
        content_slides = self.slides[2:-1]
        if not content_slides:
            raise ValueError(
                "Presentation must contain at least one content slide between agenda and conclusion"
            )

        for idx, slide in enumerate(content_slides, start=2):
            if slide.type != SlideType.CONTENT:
                raise ValueError(
                    f"Slide at position {idx + 1} must be of type '{SlideType.CONTENT}', "
                    f"but got '{slide.type}'"
                )

        # Validate that at most one question exists
        questions = [slide for slide in self.slides if slide.question is not None]
        if len(questions) > 1:
            raise ValueError(
                f"Presentation can contain at most one question, but found {len(questions)}"
            )

        # Validate question is in a content slide (middle of presentation)
        if questions:
            question_slide = questions[0]
            if question_slide.type != SlideType.CONTENT:
                raise ValueError(
                    "Questions can only be included in content slides, "
                    f"but found question in {question_slide.type} slide"
                )

        return self
