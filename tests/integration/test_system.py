import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        """Test that root endpoint returns 200."""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK

    def test_root_returns_api_info(self, client: TestClient):
        """Test that root endpoint returns API information."""
        response = client.get("/")

        data = response.json()
        assert data["message"] == "AI Slide Deck Generation Service"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
        assert data["api"] == "/api/v1"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Test that health endpoint returns 200."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

    def test_health_returns_status_ok(self, client: TestClient):
        """Test that health endpoint returns status ok."""
        response = client.get("/health")

        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_environment(self, client: TestClient):
        """Test that health endpoint returns environment."""
        response = client.get("/health")

        data = response.json()
        assert "environment" in data

    def test_health_returns_llm_provider(self, client: TestClient):
        """Test that health endpoint returns LLM provider info."""
        response = client.get("/health")

        data = response.json()
        assert "llm_provider" in data
        assert "default_model" in data


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema_available(self, client: TestClient):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui_available(self, client: TestClient):
        """Test that Swagger UI is available."""
        response = client.get("/docs")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_redoc_available(self, client: TestClient):
        """Test that ReDoc is available."""
        response = client.get("/redoc")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_preflight_request(self, client: TestClient):
        """Test that CORS preflight requests are handled."""
        response = client.options(
            "/api/v1/slide",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Should not return 405 Method Not Allowed
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present in response."""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == status.HTTP_200_OK
        # CORS headers should be present for allowed origin
        assert "access-control-allow-origin" in response.headers


class TestNotFound:
    """Tests for 404 handling."""

    def test_unknown_endpoint_returns_404(self, client: TestClient):
        """Test that unknown endpoints return 404."""
        response = client.get("/unknown/endpoint")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unknown_api_version_returns_404(self, client: TestClient):
        """Test that unknown API version returns 404."""
        response = client.get("/api/v2/slide")

        assert response.status_code == status.HTTP_404_NOT_FOUND
