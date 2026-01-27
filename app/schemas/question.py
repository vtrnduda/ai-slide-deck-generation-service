from typing import List
from pydantic import BaseModel, Field, model_validator


class Question(BaseModel):
    """
    Multiple choice question model for optional exercise slides.

    Represents a learning exercise that can be included in the middle
    of content slides to reinforce learning.
    """

    prompt: str = Field(
        ...,
        min_length=10,
        description="The question statement related to the lesson content",
        examples=["What was the main cause of the French Revolution?"],
    )
    options: List[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of answer options (typically 4 options: A, B, C, D)",
        examples=[
            [
                "A) Economic crisis",
                "B) Religious conflict",
                "C) Political reform",
                "D) Social inequality",
            ]
        ],
    )
    answer: str = Field(
        ...,
        description=(
            "The correct answer. Must be exactly identical to one of the options. "
            "Can be the option text itself or its label (e.g., 'C' or 'C) Political reform')."
        ),
        examples=["C", "C) Political reform"],
    )

    @model_validator(mode="after")
    def validate_answer_in_options(self) -> "Question":
        """
        Validate that the answer exists in the options list.

        This prevents LLM hallucinations where the answer doesn't match any option.
        """
        # Check if answer matches exactly or matches an option label (e.g., "A", "B", "C")
        answer_normalized = self.answer.strip()
        options_normalized = [opt.strip() for opt in self.options]

        # Check exact match
        if answer_normalized in options_normalized:
            return self

        # Check if answer is a single letter that matches option labels
        if len(answer_normalized) == 1 and answer_normalized.isalpha():
            option_labels = [opt[0] if opt else "" for opt in options_normalized]
            if answer_normalized.upper() in [label.upper() for label in option_labels]:
                return self

        raise ValueError(
            f"Answer '{self.answer}' must match one of the provided options: {self.options}"
        )
