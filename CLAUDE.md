# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Second Brain is an AI-powered knowledge management system with three core modules:
- **AI Chat**: Multi-model conversations with Chat and Search modes
- **Intelligent Agents**: Deep Research automation using Perplexity API
- **Knowledge Base (Space)**: Document management with AI-enhanced interactions

### Important Design Decision: Conversation-Space Relationship

**Key Concept**: Not all conversations are associated with a Space.

- **AI Chat Page Conversations**: These are standalone conversations (space_id = None), similar to a search engine tool for quick information lookup
- **Space-Associated Conversations**: Only conversations created through:
  - Deep Research agent (automatically creates a Space)
  - Within a specific Space by the user
  
This design allows AI Chat to function as a general-purpose tool while maintaining Space as a focused knowledge management area.

### Agent System Design

**Key Concept**: The Agent model supports both simple Prompt-based agents and future LangGraph-based agents.

**Agent Types**:
1. **Official Agents** (user_id = None):
   - Prompt Agents: Pre-defined prompts for specific tasks
   - LangGraph Agents (future): Complex multi-step agents with tool usage
   
2. **User Custom Agents** (user_id = specific user):
   - Users can create their own prompt-based agents
   
**Technical Implementation**:
- `agent_type` field distinguishes between different agent types (research, analysis, custom, etc.)
- `config` JSON field stores flexible configuration (simple for Prompt agents, complex for LangGraph agents)
- `tools` field will store tool chains for LangGraph agents
- `prompt_template` field for prompt-based agents
- `capabilities` field indicates what the agent can do

This design ensures backward compatibility while allowing future expansion to LangGraph agents.

## Development Commands

### Environment Setup
```bash
# First time setup
cd backend
cp .env.example .env  # Then add at least one AI API key
./scripts/start.sh    # Creates directories, starts services, runs migrations

# Manual setup if script fails
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Common Development Tasks

**IMPORTANT**: This project uses `uv` for package management, not pip!

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Restart backend (after code changes)
docker-compose restart backend

# Install dependencies (using uv)
uv pip install -r requirements.txt  # From requirements file
uv pip install package_name         # Install single package

# Run tests (using uv)
docker-compose exec backend uv run pytest
docker-compose exec backend uv run pytest -v  # Verbose output
docker-compose exec backend uv run pytest tests/test_file.py::test_function

# Code formatting and linting (using uv)
docker-compose exec backend uv run black app/
docker-compose exec backend uv run ruff check app/ --fix

# Type checking (using uv)
docker-compose exec backend uv run mypy app/

# Access services
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/v1/docs
# - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
# - PostgreSQL: localhost:5432 (secondbrain/secondbrain123)
# - Redis: localhost:6379
# - Qdrant: localhost:6333
```

## Architecture Patterns

### API Layer Structure
```
app/api/v1/
├── api.py              # Main router aggregator
└── endpoints/
    ├── auth.py         # Authentication (login, register, tokens)
    ├── chat.py         # AI conversations (streaming, multi-model)
    ├── agents.py       # AI agents (Deep Research)
    ├── spaces.py       # Knowledge spaces
    ├── documents.py    # Document upload/management
    └── ...
```

### Service Layer Pattern
All business logic is in `app/services/`:
- AI providers are abstracted with a common interface in `ai_service.py`
- Each service handles a specific domain (documents, conversations, etc.)
- Services use dependency injection via FastAPI

### Database Access Pattern
- Models defined in `app/models/models.py` using SQLAlchemy ORM
- CRUD operations in `app/crud/` provide database access layer
- Schemas in `app/schemas/` define API request/response models
- All database operations are async using asyncpg

### AI Provider Integration
```python
# Example: Adding a new AI provider
class NewProvider(AIProvider):
    async def chat(self, messages, model, **kwargs) -> str:
        # Implement sync chat
    
    async def stream_chat(self, messages, model, **kwargs) -> AsyncGenerator[str, None]:
        # Implement streaming
    
    async def get_embedding(self, text, model=None) -> List[float]:
        # Implement embeddings
```

### Vector Search Pattern
- Documents are chunked and embedded on upload
- Embeddings stored in Qdrant with metadata
- Search combines vector similarity with filters
- Used for Space-specific AI conversations

### Authentication Flow
- JWT tokens with access/refresh pattern
- Tokens stored in Redis for validation
- User context available via `get_current_user` dependency
- Rate limiting per user/endpoint

## Key Implementation Details

### Streaming Responses
Chat endpoints support Server-Sent Events (SSE) for real-time streaming:
```python
async def stream_response():
    async for chunk in ai_service.stream_chat(...):
        yield f"data: {json.dumps({'content': chunk})}\n\n"
```

### File Processing Pipeline
1. Upload to MinIO with unique ID
2. Extract text based on file type (PDF, DOCX, etc.)
3. Chunk text with overlap for context
4. Generate embeddings via AI provider
5. Store in Qdrant with document metadata

### Deep Research Agent
- Accepts topic and mode (general/academic)
- Calls Perplexity Deep Research API
- Auto-creates Space with research results
- Saves sources as documents in Space

### Message Branching
Conversations support branching for alternative responses:
- `parent_message_id` links messages
- `branch_id` groups alternative responses
- UI can show/switch between branches

## Environment Variables

Required in `.env`:
```bash
# At least one AI provider key required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...

# Required for search/research features
PERPLEXITY_API_KEY=pplx-...

# Database (auto-configured in docker-compose)
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=your-secret-key-here
```

## Common Patterns

### Adding New Endpoints
1. Create schema in `app/schemas/`
2. Add CRUD operations in `app/crud/` if needed
3. Implement business logic in `app/services/`
4. Create endpoint in `app/api/v1/endpoints/`
5. Include router in `app/api/v1/api.py`

### Error Handling
- Use FastAPI's HTTPException for API errors
- Services raise custom exceptions
- Global exception handlers in `main.py`
- Async context managers for resource cleanup

### Testing Approach
- Use pytest with async support
- Test database with transactions rollback
- Mock external APIs (AI providers, storage)
- Integration tests for full workflows

## Performance Considerations

- Database queries use eager loading to avoid N+1
- Redis caches frequent queries (user data, configs)
- Streaming responses for large AI outputs
- Background tasks for heavy processing
- Connection pooling for all services