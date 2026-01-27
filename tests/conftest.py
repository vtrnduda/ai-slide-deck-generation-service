import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_llm_engine
from app.schemas import Presentation, Slide, Question
from app.schemas.enums import SlideType
from app.services import LLMEngine


@pytest.fixture
def sample_request_data() -> dict:
    """Valid request data for slide generation."""
    return {
        "topic": "Photosynthesis",
        "grade": "7th grade",
        "context": "Focus on light-dependent reactions",
        "n_slides": 3,
    }


@pytest.fixture
def sample_request_minimal() -> dict:
    """Minimal valid request data (only required fields)."""
    return {
        "topic": "Math",
        "grade": "5th grade",
        "n_slides": 1,
    }


@pytest.fixture
def sample_question() -> Question:
    """Sample question for testing."""
    return Question(
        prompt="What is the primary pigment in photosynthesis?",
        options=[
            "A) Chlorophyll",
            "B) Melanin",
            "C) Hemoglobin",
            "D) Carotene",
        ],
        answer="A) Chlorophyll",
    )


@pytest.fixture
def sample_slides(sample_question: Question) -> list[Slide]:
    """Sample slides following the required structure."""
    return [
        Slide(
            type=SlideType.TITLE,
            title="Introduction to Photosynthesis",
            content="Understanding how plants convert light into energy",
        ),
        Slide(
            type=SlideType.AGENDA,
            title="What We'll Learn",
            content="- Light reactions\n- Dark reactions\n- Importance",
        ),
        Slide(
            type=SlideType.CONTENT,
            title="Light-Dependent Reactions",
            content="Occurs in thylakoid membranes",
            image="photosynthesis diagram",
        ),
        Slide(
            type=SlideType.CONTENT,
            title="Key Concepts",
            content="Chlorophyll captures light energy",
            question=sample_question,
        ),
        Slide(
            type=SlideType.CONTENT,
            title="The Calvin Cycle",
            content="Also known as light-independent reactions",
        ),
        Slide(
            type=SlideType.CONCLUSION,
            title="Summary",
            content="Photosynthesis is essential for life on Earth",
        ),
    ]


@pytest.fixture
def sample_presentation(sample_slides: list[Slide]) -> Presentation:
    """Sample complete presentation."""
    return Presentation(
        topic="Photosynthesis",
        grade="7th grade",
        slides=sample_slides,
    )


@pytest.fixture
def mock_llm_engine(sample_presentation: Presentation) -> MagicMock:
    """Mock LLMEngine that returns sample presentation."""
    mock = MagicMock(spec=LLMEngine)
    mock.generate_presentation = AsyncMock(return_value=sample_presentation)

    async def mock_stream():
        yield sample_presentation

    mock.stream_presentation = MagicMock(return_value=mock_stream())
    return mock


@pytest.fixture
def mock_llm_engine_error() -> MagicMock:
    """Mock LLMEngine that raises an error."""
    from app.services import LLMGenerationError

    mock = MagicMock(spec=LLMEngine)
    mock.generate_presentation = AsyncMock(side_effect=LLMGenerationError("API Error"))
    return mock


@pytest.fixture
def client() -> TestClient:
    """Test client without mocks (for system endpoints)."""
    return TestClient(app)


@pytest.fixture
def client_with_mock_llm(mock_llm_engine: MagicMock) -> TestClient:
    """Test client with mocked LLM engine."""
    app.dependency_overrides[get_llm_engine] = lambda: mock_llm_engine
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_error_llm(mock_llm_engine_error: MagicMock) -> TestClient:
    """Test client with LLM engine that raises errors."""
    app.dependency_overrides[get_llm_engine] = lambda: mock_llm_engine_error
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
