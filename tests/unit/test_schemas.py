import pytest
from pydantic import ValidationError

from app.schemas import LessonRequest, Presentation, Slide, Question
from app.schemas.enums import SlideType


class TestLessonRequest:
    """Tests for LessonRequest schema validation."""

    def test_valid_request(self, sample_request_data: dict):
        """Test that valid data creates a request successfully."""
        request = LessonRequest(**sample_request_data)

        assert request.topic == "Photosynthesis"
        assert request.grade == "7th grade"
        assert request.context == "Focus on light-dependent reactions"
        assert request.n_slides == 3

    def test_minimal_request(self, sample_request_minimal: dict):
        """Test request with only required fields."""
        request = LessonRequest(**sample_request_minimal)

        assert request.topic == "Math"
        assert request.grade == "5th grade"
        assert request.context == ""  # Default empty string
        assert request.n_slides == 1

    def test_topic_whitespace_sanitization(self):
        """Test that topic whitespace is stripped."""
        request = LessonRequest(
            topic="  Photosynthesis  ",
            grade="7th grade",
            n_slides=3,
        )
        assert request.topic == "Photosynthesis"

    def test_topic_too_short(self):
        """Test that topic with less than 3 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(topic="AB", grade="7th grade", n_slides=3)

        assert "topic" in str(exc_info.value)

    def test_topic_too_long(self):
        """Test that topic exceeding 100 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(topic="A" * 101, grade="7th grade", n_slides=3)

        assert "topic" in str(exc_info.value)

    def test_topic_empty_after_strip(self):
        """Test that topic with only whitespace fails."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(topic="   ", grade="7th grade", n_slides=3)

        assert "empty" in str(exc_info.value).lower()

    def test_grade_whitespace_sanitization(self):
        """Test that grade whitespace is stripped."""
        request = LessonRequest(
            topic="Math",
            grade="  7th grade  ",
            n_slides=3,
        )
        assert request.grade == "7th grade"

    def test_grade_empty_after_strip(self):
        """Test that grade with only whitespace fails."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(topic="Math", grade="   ", n_slides=3)

        assert "empty" in str(exc_info.value).lower()

    def test_context_sanitization(self):
        """Test that context whitespace is stripped."""
        request = LessonRequest(
            topic="Math",
            grade="7th grade",
            context="  Some context  ",
            n_slides=3,
        )
        assert request.context == "Some context"

    def test_context_too_long(self):
        """Test that context exceeding 2000 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(
                topic="Math",
                grade="7th grade",
                context="A" * 2001,
                n_slides=3,
            )

        assert "context" in str(exc_info.value)

    def test_n_slides_minimum(self):
        """Test that n_slides must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(topic="Math", grade="7th grade", n_slides=0)

        assert "n_slides" in str(exc_info.value)

    def test_n_slides_maximum(self):
        """Test that n_slides cannot exceed 15."""
        with pytest.raises(ValidationError) as exc_info:
            LessonRequest(topic="Math", grade="7th grade", n_slides=16)

        assert "n_slides" in str(exc_info.value)

    def test_n_slides_valid_range(self):
        """Test n_slides at boundary values."""
        request_min = LessonRequest(topic="Math", grade="7th", n_slides=1)
        request_max = LessonRequest(topic="Math", grade="7th", n_slides=15)

        assert request_min.n_slides == 1
        assert request_max.n_slides == 15

    def test_missing_required_field(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ValidationError):
            LessonRequest(topic="Math", grade="7th grade")  # Missing n_slides


class TestQuestion:
    """Tests for Question schema validation."""

    def test_valid_question(self, sample_question: Question):
        """Test that valid question data creates successfully."""
        assert sample_question.prompt == "What is the primary pigment in photosynthesis?"
        assert len(sample_question.options) == 4
        assert sample_question.answer == "A) Chlorophyll"

    def test_answer_exact_match(self):
        """Test answer matches option exactly."""
        question = Question(
            prompt="What is 2+2?",
            options=["3", "4", "5", "6"],
            answer="4",
        )
        assert question.answer == "4"

    def test_answer_label_match(self):
        """Test answer matches option label (A, B, C, D)."""
        question = Question(
            prompt="What is 2+2?",
            options=["A) 3", "B) 4", "C) 5", "D) 6"],
            answer="B",
        )
        assert question.answer == "B"

    def test_answer_not_in_options(self):
        """Test that answer not matching any option fails."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                prompt="What is 2+2?",
                options=["3", "4", "5", "6"],
                answer="7",
            )

        assert "answer" in str(exc_info.value).lower()

    def test_prompt_too_short(self):
        """Test that prompt with less than 10 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                prompt="Short?",
                options=["A", "B"],
                answer="A",
            )

        assert "prompt" in str(exc_info.value)

    def test_options_minimum(self):
        """Test that at least 2 options are required."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                prompt="What is the answer?",
                options=["Only one"],
                answer="Only one",
            )

        assert "options" in str(exc_info.value)

    def test_options_maximum(self):
        """Test that maximum 5 options allowed."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                prompt="What is the answer?",
                options=["A", "B", "C", "D", "E", "F"],
                answer="A",
            )

        assert "options" in str(exc_info.value)


class TestSlide:
    """Tests for Slide schema validation."""

    def test_valid_content_slide(self):
        """Test valid content slide creation."""
        slide = Slide(
            type=SlideType.CONTENT,
            title="Test Title",
            content="Test content here",
        )

        assert slide.type == SlideType.CONTENT
        assert slide.title == "Test Title"
        assert slide.content == "Test content here"
        assert slide.image is None
        assert slide.question is None

    def test_content_slide_with_image(self):
        """Test content slide with image query."""
        slide = Slide(
            type=SlideType.CONTENT,
            title="Test Title",
            content="Test content",
            image="test image query",
        )

        assert slide.image == "test image query"

    def test_content_slide_with_question(self, sample_question: Question):
        """Test content slide with question."""
        slide = Slide(
            type=SlideType.CONTENT,
            title="Test Title",
            content="Test content",
            question=sample_question,
        )

        assert slide.question is not None
        assert slide.question.prompt == sample_question.prompt

    def test_title_slide_no_question(self, sample_question: Question):
        """Test that title slide cannot have question."""
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                type=SlideType.TITLE,
                title="Title Slide",
                content="Content",
                question=sample_question,
            )

        assert "question" in str(exc_info.value).lower()

    def test_agenda_slide_no_question(self, sample_question: Question):
        """Test that agenda slide cannot have question."""
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                type=SlideType.AGENDA,
                title="Agenda",
                content="Content",
                question=sample_question,
            )

        assert "question" in str(exc_info.value).lower()

    def test_conclusion_slide_no_question(self, sample_question: Question):
        """Test that conclusion slide cannot have question."""
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                type=SlideType.CONCLUSION,
                title="Summary",
                content="Content",
                question=sample_question,
            )

        assert "question" in str(exc_info.value).lower()

    def test_title_too_long(self):
        """Test that title exceeding 200 chars fails."""
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                type=SlideType.CONTENT,
                title="A" * 201,
                content="Content",
            )

        assert "title" in str(exc_info.value)

    def test_empty_title(self):
        """Test that empty title fails."""
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                type=SlideType.CONTENT,
                title="",
                content="Content",
            )

        assert "title" in str(exc_info.value)

    def test_empty_content(self):
        """Test that empty content fails."""
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                type=SlideType.CONTENT,
                title="Title",
                content="",
            )

        assert "content" in str(exc_info.value)


class TestPresentation:
    """Tests for Presentation schema validation."""

    def test_valid_presentation(self, sample_presentation: Presentation):
        """Test valid presentation creation."""
        assert sample_presentation.topic == "Photosynthesis"
        assert sample_presentation.grade == "7th grade"
        assert len(sample_presentation.slides) == 6

    def test_presentation_structure_first_slide_title(self):
        """Test that first slide must be title."""
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                topic="Test",
                grade="7th",
                slides=[
                    Slide(type=SlideType.CONTENT, title="Wrong", content="Content"),
                    Slide(type=SlideType.AGENDA, title="Agenda", content="Content"),
                    Slide(type=SlideType.CONTENT, title="Content", content="Content"),
                    Slide(type=SlideType.CONCLUSION, title="End", content="Content"),
                ],
            )

        assert "title" in str(exc_info.value).lower()

    def test_presentation_structure_second_slide_agenda(self):
        """Test that second slide must be agenda."""
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                topic="Test",
                grade="7th",
                slides=[
                    Slide(type=SlideType.TITLE, title="Title", content="Content"),
                    Slide(type=SlideType.CONTENT, title="Wrong", content="Content"),
                    Slide(type=SlideType.CONTENT, title="Content", content="Content"),
                    Slide(type=SlideType.CONCLUSION, title="End", content="Content"),
                ],
            )

        assert "agenda" in str(exc_info.value).lower()

    def test_presentation_structure_last_slide_conclusion(self):
        """Test that last slide must be conclusion."""
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                topic="Test",
                grade="7th",
                slides=[
                    Slide(type=SlideType.TITLE, title="Title", content="Content"),
                    Slide(type=SlideType.AGENDA, title="Agenda", content="Content"),
                    Slide(type=SlideType.CONTENT, title="Content", content="Content"),
                    Slide(type=SlideType.CONTENT, title="Wrong", content="Content"),
                ],
            )

        assert "conclusion" in str(exc_info.value).lower()

    def test_presentation_middle_slides_must_be_content(self):
        """Test that middle slides must be content type."""
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                topic="Test",
                grade="7th",
                slides=[
                    Slide(type=SlideType.TITLE, title="Title", content="Content"),
                    Slide(type=SlideType.AGENDA, title="Agenda", content="Content"),
                    Slide(type=SlideType.TITLE, title="Wrong", content="Content"),  # Wrong type
                    Slide(type=SlideType.CONCLUSION, title="End", content="Content"),
                ],
            )

        assert "content" in str(exc_info.value).lower()

    def test_presentation_minimum_slides(self):
        """Test that presentation needs at least title, agenda, content, conclusion."""
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                topic="Test",
                grade="7th",
                slides=[
                    Slide(type=SlideType.TITLE, title="Title", content="Content"),
                    Slide(type=SlideType.CONCLUSION, title="End", content="Content"),
                ],
            )

        # Should fail because missing agenda and content
        assert exc_info.value is not None

    def test_presentation_max_one_question(self, sample_question: Question):
        """Test that presentation can have at most one question."""
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                topic="Test",
                grade="7th",
                slides=[
                    Slide(type=SlideType.TITLE, title="Title", content="Content"),
                    Slide(type=SlideType.AGENDA, title="Agenda", content="Content"),
                    Slide(
                        type=SlideType.CONTENT,
                        title="Content 1",
                        content="Content",
                        question=sample_question,
                    ),
                    Slide(
                        type=SlideType.CONTENT,
                        title="Content 2",
                        content="Content",
                        question=sample_question,  # Second question - should fail
                    ),
                    Slide(type=SlideType.CONCLUSION, title="End", content="Content"),
                ],
            )

        assert "question" in str(exc_info.value).lower()

    def test_presentation_empty_slides(self):
        """Test that empty slides list fails."""
        with pytest.raises(ValidationError):
            Presentation(
                topic="Test",
                grade="7th",
                slides=[],
            )
