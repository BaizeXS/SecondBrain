# SecondBrain Backend

AI-powered knowledge management system backend service.

## 📁 Directory Structure

```
backend/
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   ├── core/              # Core utilities (auth, config, database)
│   ├── crud/              # Database CRUD operations
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic services
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── tools/                  # Development and testing tools
│   ├── test_*.py          # API testing scripts
│   ├── api_tester.html    # Browser-based API tester
│   └── serve_test_page.py # Test page server
├── examples/               # Example scripts and demos
│   ├── create_demo_data.py     # Demo data creation
│   ├── quick_demo_setup.py     # Quick setup script
│   └── init_ai_providers.py    # AI provider initialization
├── scripts/                # Utility scripts
│   ├── start.sh           # Service startup script
│   ├── setup_demo.sh      # Demo environment setup
│   └── demo_fixes.sh      # Demo fixes script
├── docs/                   # Documentation
│   ├── API guides         # API documentation
│   ├── Architecture       # System architecture docs
│   └── Integration guides # Frontend integration guides
├── alembic/               # Database migrations
├── htmlcov/               # Test coverage reports
└── docker-compose.yml     # Docker services configuration
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (if running locally)
- uv package manager

### Setup

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Add your OpenRouter API key to .env
# OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 3. Start all services
./scripts/start.sh

# 4. Create demo data (optional)
docker exec secondbrain-backend python examples/create_demo_data.py
```

### Access Services

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/v1/docs
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- PostgreSQL: localhost:5432 (secondbrain/secondbrain123)

## 📖 Documentation

- [Quick Start](docs/QUICKSTART.md) - 快速开始指南
- [API Reference](docs/API_COMPLETE_REFERENCE.md) - 完整API文档（104个端点）
- [Architecture](docs/ARCHITECTURE_COMPLETE.md) - 系统架构说明
- [Frontend Guide](docs/FRONTEND_INTEGRATION_GUIDE.md) - 前端集成指南
- [Deployment](docs/DEPLOYMENT_GUIDE.md) - 生产部署指南

## 🧪 Testing

### Run Tests

```bash
# Unit tests
docker-compose exec backend uv run pytest tests/unit/

# Integration tests
docker-compose exec backend uv run pytest tests/integration/

# All tests with coverage
docker-compose exec backend uv run pytest --cov=app
```

### Test Tools

- `tools/test_all_apis_100_percent.py` - Complete API coverage test
- `tools/api_tester.html` - Browser-based API testing interface
- `tools/test_backend_complete.py` - Backend functionality test

## 🛠️ Development

### Code Style

```bash
# Format code
docker-compose exec backend uv run black app/

# Lint code
docker-compose exec backend uv run ruff check app/

# Type checking
docker-compose exec backend uv run mypy app/
```

### Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head
```

## 📊 API Overview

### Core Modules

- **Auth**: User authentication and authorization
- **Chat**: AI-powered conversations with streaming
- **Spaces**: Knowledge space management
- **Documents**: File upload and management
- **Notes**: Note-taking with AI enhancement
- **Agents**: AI agents including Deep Research

### Key Features

- Multi-model AI support via OpenRouter
- Real-time streaming responses
- Vector search with Qdrant
- File processing with MinIO
- Redis-based caching

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Ensure no IDE warnings
5. Run formatter and linter before committing

## 📝 License

Copyright © 2024 SecondBrain Team. All rights reserved.
