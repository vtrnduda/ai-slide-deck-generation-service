# AI Slide Deck Generation Service

Backend service in Python using FastAPI to generate educational lesson slide decks based on a topic, student grade, and additional context. Powered by LangChain and supporting multiple LLM providers (OpenAI and Google Gemini).

## 📋 Requirements

### Local Development
- Python 3.10 or higher
- Poetry (dependency manager)

### Docker (Alternative)
- Docker 20.10+
- Docker Compose v2+

### Common
- Git
- API Key for at least one LLM provider:
  - OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
  - Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-slide-deck-generation-service
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

**Linux/WSL:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your API keys:

```env
# At least one LLM provider API key is required
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# LLM Configuration (optional - all have defaults)
DEFAULT_LLM_PROVIDER=google
DEFAULT_MODEL=gemini-1.5-flash
DEFAULT_TEMPERATURE=0.5
DEFAULT_MAX_RETRIES=2
```

> **Note:** See `.env.example` for detailed descriptions of all available configuration options.

### 4. Run the Server

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 🐳 Running with Docker

### Prerequisites

- Docker 20.10+
- Docker Compose v2+

### Option 1: Production Mode

Build and run the production container:

```bash
# Build the image
docker compose build api

# Run the container
docker compose up api
```

Or in a single command:
```bash
docker compose up api --build
```

### Option 2: Development Mode (with hot reload)

Run with volume mounting for live code changes:

```bash
docker compose --profile dev up api-dev --build
```

Changes to files in `./app` will automatically reload the server.

### Environment Variables

Create a `.env` file before running (see `.env.example`):

```bash
cp .env.example .env
# Edit .env with your API keys
```

The container will automatically load variables from `.env`.

### Container Details

| Aspect | Value |
|--------|-------|
| Base Image | `python:3.12-slim` |
| Port | `8000` |
| User | Non-root (`appuser`) |
| Health Check | `GET /health` every 30s |

## 📖 API Documentation

Once the server is running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🌐 API Endpoints

### System Endpoints

#### `GET /`
Returns API information and available endpoints.

**Response:**
```json
{
  "message": "AI Slide Deck Generation Service",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "api": "/api/v1"
}
```

#### `GET /health`
Health check endpoint for monitoring and container health probes.

**Response:**
```json
{
  "status": "ok",
  "environment": "development",
  "llm_provider": "google",
  "default_model": "gemini-1.5-flash"
}
```

### Presentation Endpoints

#### `POST /api/v1/slide`
Generates a complete presentation with all slides at once.

**Request Body:**
```json
{
  "topic": "Photosynthesis",
  "grade": "7th grade",
  "context": "Focus on the light-dependent reactions",
  "n_slides": 5
}
```

**Response:**
```json
{
  "topic": "Photosynthesis",
  "grade": "7th grade",
  "slides": [
    {
      "type": "title",
      "title": "Introduction to Photosynthesis",
      "content": "Understanding how plants convert light into energy"
    },
    {
      "type": "agenda",
      "title": "What We'll Learn",
      "content": "• Light-dependent reactions\n• Light-independent reactions\n• Importance of photosynthesis"
    },
    {
      "type": "content",
      "title": "Light-Dependent Reactions",
      "content": "• Occurs in the thylakoid membranes\n• Converts light energy to chemical energy\n• Produces ATP and NADPH",
      "image": "photosynthesis diagram"
    },
    {
      "type": "content",
      "title": "Key Concepts",
      "content": "• Chlorophyll captures light\n• Water is split\n• Oxygen is released",
      "question": {
        "prompt": "Where do light-dependent reactions occur?",
        "options": [
          "A) Stroma",
          "B) Thylakoid membranes",
          "C) Mitochondria",
          "D) Nucleus"
        ],
        "answer": "B) Thylakoid membranes"
      }
    },
    {
      "type": "conclusion",
      "title": "Summary",
      "content": "Photosynthesis is essential for life on Earth..."
    }
  ]
}
```

**Note:** Total slides = `n_slides` + 3 (title + agenda + conclusion)

#### `POST /api/v1/streaming`
Streams the presentation slide by slide using Server-Sent Events (SSE).

**Request Body:** Same as `/api/v1/slide`

**Response:** Server-Sent Events stream

## 📁 Project Structure

```
ai-slide-deck-generation-service/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   │
│   ├── api/                       # API Layer (Controllers)
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Dependency injection
│   │   ├── system.py              # System endpoints (/health, /)
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py       # Business endpoints (/slide, /streaming)
│   │
│   ├── core/                      # Core Configuration
│   │   ├── __init__.py
│   │   └── config.py              # Pydantic Settings (environment variables)
│   │
│   ├── schemas/                   # Domain Models (Pydantic Schemas)
│   │   ├── __init__.py
│   │   ├── enums.py               # SlideType enum
│   │   ├── request.py             # LessonRequest model
│   │   ├── question.py            # Question model
│   │   ├── slide.py               # Slide model
│   │   └── presentation.py        # Presentation model
│   │
│   └── services/                  # Business Logic Layer
│       ├── __init__.py
│       ├── prompts.py             # Prompt templates
│       └── llm_engine.py          # LLM orchestration with LangChain
│
├── tests/                         # Test suite
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Poetry dependencies and tool configs
├── Dockerfile                     # Production Docker image
├── Dockerfile.dev                 # Development Docker image (hot reload)
├── docker-compose.yml             # Docker Compose configuration
├── .dockerignore                  # Docker build exclusions
└── README.md
```

## 🔧 Configuration

### Environment Variables

All configuration is done through environment variables (via `.env` file):

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | `None` | At least one LLM key |
| `GOOGLE_API_KEY` | Google Gemini API key | `None` | At least one LLM key |
| `ENVIRONMENT` | Environment (development/staging/production) | `development` | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` | No |
| `DEFAULT_LLM_PROVIDER` | Default LLM provider (`openai` or `google`) | `google` | No |
| `DEFAULT_MODEL` | Default model name | `gemini-1.5-flash` | No |
| `DEFAULT_TEMPERATURE` | Sampling temperature (0.0-2.0) | `0.5` | No |
| `DEFAULT_MAX_RETRIES` | Maximum retry attempts | `2` | No |
| `DEFAULT_TIMEOUT` | Request timeout in seconds | `None` | No |

### LLM Provider Selection

The system automatically selects the LLM provider based on:
1. `DEFAULT_LLM_PROVIDER` setting (if both keys are available)
2. Available API keys (uses the provider with a configured key)
3. Falls back to Google if only one key is available

## 🛠️ Development

### Running in Development Mode

```bash
poetry run uvicorn app.main:app --reload
```

The `--reload` flag enables auto-reload on code changes.

### Running Tests

```bash
poetry run pytest
```

With coverage:
```bash
poetry run pytest --cov=app
```

### Code Quality Tools

**Format code:**
```bash
poetry run black .
```

**Lint code:**
```bash
poetry run ruff check .
```

**Type checking:**
```bash
poetry run mypy app
```

## 📚 Slide Structure

Each presentation follows a strict structure:

1. **Title Slide** (`type: "title"`)
   - Introduces the lesson topic

2. **Agenda Slide** (`type: "agenda"`)
   - Lists main points to be covered

3. **Content Slides** (`type: "content"`)
   - Number specified by `n_slides` parameter
   - May include optional `image` field (search query)
   - One slide may include optional `question` field (multiple choice)

4. **Conclusion Slide** (`type: "conclusion"`)
   - Summarizes key points

**Total slides = n_slides + 3**

## 📄 License

MIT License - see LICENSE file for details