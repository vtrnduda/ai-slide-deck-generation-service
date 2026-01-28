from unittest.mock import AsyncMock, MagicMock

from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies import get_llm_engine
from app.main import app
from app.services import LLMValidationError


class TestGenerateSlides:
    """Tests for the /api/v1/slide endpoint."""

    def test_generate_slides_success(
        self,
        client_with_mock_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test successful slide generation."""
        response = client_with_mock_llm.post("/api/v1/slide", json=sample_request_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "topic" in data
        assert "grade" in data
        assert "slides" in data
        assert len(data["slides"]) > 0

    def test_generate_slides_minimal_request(
        self,
        client_with_mock_llm: TestClient,
        sample_request_minimal: dict,
    ):
        """Test slide generation with minimal request data."""
        response = client_with_mock_llm.post("/api/v1/slide", json=sample_request_minimal)

        assert response.status_code == status.HTTP_200_OK

    def test_generate_slides_validates_structure(
        self,
        client_with_mock_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test that response follows expected structure."""
        response = client_with_mock_llm.post("/api/v1/slide", json=sample_request_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        slides = data["slides"]

        # Verify structure: title, agenda, content..., conclusion
        assert slides[0]["type"] == "title"
        assert slides[1]["type"] == "agenda"
        assert slides[-1]["type"] == "conclusion"

        # Middle slides should be content
        for slide in slides[2:-1]:
            assert slide["type"] == "content"

    def test_generate_slides_invalid_topic_too_short(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that short topic is rejected."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "AB",  # Too short (< 3)
                "grade": "7th grade",
                "n_slides": 3,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_slides_invalid_n_slides_zero(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that n_slides=0 is rejected."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Mathematics",
                "grade": "7th grade",
                "n_slides": 0,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_slides_invalid_n_slides_exceeds_max(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that n_slides > 15 is rejected."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Mathematics",
                "grade": "7th grade",
                "n_slides": 16,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_slides_missing_required_field(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that missing required fields are rejected."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Mathematics",
                "grade": "7th grade",
                # Missing n_slides
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_slides_context_too_long(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that context exceeding 2000 chars is rejected."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Mathematics",
                "grade": "7th grade",
                "context": "A" * 2001,
                "n_slides": 3,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_slides_llm_generation_error(
        self,
        client_with_error_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test that LLM generation errors return 500."""
        response = client_with_error_llm.post("/api/v1/slide", json=sample_request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "AI generation failed" in response.json()["detail"]

    def test_generate_slides_llm_validation_error(
        self,
        sample_request_data: dict,
    ):
        """Test that LLM validation errors return 422."""
        mock_engine = MagicMock()
        mock_engine.generate_presentation = AsyncMock(
            side_effect=LLMValidationError("Schema mismatch")
        )

        app.dependency_overrides[get_llm_engine] = lambda: mock_engine
        client = TestClient(app)

        response = client.post("/api/v1/slide", json=sample_request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "schema" in response.json()["detail"].lower()

        app.dependency_overrides.clear()


class TestStreamingEndpoint:
    """Tests for the /api/v1/streaming endpoint."""

    def test_streaming_returns_event_stream(
        self,
        client_with_mock_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test that streaming endpoint returns event stream."""
        response = client_with_mock_llm.post(
            "/api/v1/streaming",
            json=sample_request_data,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_streaming_returns_data(
        self,
        client_with_mock_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test that streaming returns valid data chunks."""
        response = client_with_mock_llm.post(
            "/api/v1/streaming",
            json=sample_request_data,
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.text

        # Should contain SSE data
        assert "data:" in content

    def test_streaming_ends_with_done(
        self,
        client_with_mock_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test that streaming ends with done event."""
        response = client_with_mock_llm.post(
            "/api/v1/streaming",
            json=sample_request_data,
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.text

        # Should end with done event
        assert "[DONE]" in content

    def test_streaming_invalid_request(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that invalid request returns validation error."""
        response = client_with_mock_llm.post(
            "/api/v1/streaming",
            json={
                "topic": "AB",  # Too short
                "grade": "7th grade",
                "n_slides": 3,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_streaming_has_correct_headers(
        self,
        client_with_mock_llm: TestClient,
        sample_request_data: dict,
    ):
        """Test that streaming response has correct headers."""
        response = client_with_mock_llm.post(
            "/api/v1/streaming",
            json=sample_request_data,
        )

        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("x-accel-buffering") == "no"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_topic_with_special_characters(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test topic with special characters."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Math: Addition & Subtraction (Basic)",
                "grade": "3rd grade",
                "n_slides": 2,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_topic_with_unicode(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test topic with unicode characters."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Introduo Matemtica",
                "grade": "7 ano",
                "n_slides": 3,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_n_slides_boundary_min(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test minimum n_slides (1)."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Quick Topic",
                "grade": "5th grade",
                "n_slides": 1,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_n_slides_boundary_max(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test maximum n_slides (15)."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Comprehensive Topic",
                "grade": "12th grade",
                "n_slides": 15,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_empty_context_allowed(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that empty context is allowed."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "Mathematics",
                "grade": "7th grade",
                "context": "",
                "n_slides": 3,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_whitespace_only_topic_rejected(
        self,
        client_with_mock_llm: TestClient,
    ):
        """Test that whitespace-only topic is rejected."""
        response = client_with_mock_llm.post(
            "/api/v1/slide",
            json={
                "topic": "   ",
                "grade": "7th grade",
                "n_slides": 3,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
