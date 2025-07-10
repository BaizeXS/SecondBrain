# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Second Brain is an AI-powered knowledge management system that helps users efficiently collect, organize, and deeply apply various learning materials. The project consists of a FastAPI backend with PostgreSQL, Redis, MinIO, and Qdrant for data management and AI capabilities.

## Architecture Overview

The backend follows a three-layer architecture:

1. **API Layer** (`app/api/v1/endpoints/`) - HTTP request handling, validation, authentication
2. **Service Layer** (`app/services/`) - Business logic, cross-entity operations, third-party integrations
3. **CRUD Layer** (`app/crud/`) - Database operations, query building, data access

Key components:
- **Authentication**: JWT-based with user role management
- **Document Management**: Upload, storage (MinIO), content extraction, vector search (Qdrant)
- **AI Services**: Multi-provider support (OpenAI, Anthropic, Google, DeepSeek) with intelligent model selection
- **Space Management**: Knowledge spaces with collaboration and permissions
- **Conversation System**: AI chat with history management

## Development Commands

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Install dependencies (using uv)
uv sync

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Start all services with Docker Compose
docker-compose up -d

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Linting and formatting
ruff check .
ruff format .
black .

# Type checking
mypy app/
```

### Database Commands

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_crud_layer.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_crud_layer.py::test_function_name
```

## Service Configuration

The system uses environment variables for configuration. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MINIO_ENDPOINT`: MinIO server endpoint
- `QDRANT_HOST`: Qdrant server host
- `SECRET_KEY`: JWT secret key
- AI API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`

## Development Workflow

1. **Database Setup**: The project uses PostgreSQL with async SQLAlchemy. Always run migrations after model changes.

2. **Service Layer Pattern**: When adding new features, follow the three-layer architecture:
   - Define schemas in `app/schemas/`
   - Implement CRUD operations in `app/crud/`
   - Add business logic in `app/services/`
   - Create API endpoints in `app/api/v1/endpoints/`

3. **AI Service Integration**: The system intelligently selects services based on available API keys. Services have both full and simplified versions for development without API keys.

4. **Testing**: Write tests for all layers. Use pytest fixtures for database sessions and mock external services.

## Important Notes

- The project uses Python 3.12+ with async/await patterns throughout
- All database operations use async SQLAlchemy
- File uploads are stored in MinIO, with metadata in PostgreSQL
- Vector embeddings are stored in Qdrant for semantic search
- The system supports streaming responses for AI chat
- Redis is used for caching and rate limiting