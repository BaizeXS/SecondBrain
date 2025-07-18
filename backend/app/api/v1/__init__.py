"""
API v1 package.

This is the main API version for Second Brain Backend.
All endpoints are organized by feature domain and follow RESTful conventions.

Key Features:
- JWT-based authentication with refresh tokens
- Multi-model AI chat with streaming support
- Deep Research agents powered by Perplexity
- Knowledge management with Spaces
- Document processing with AI-enhanced search
- Note-taking with version control
- Real-time annotations and citations
"""

from app.api.v1.api import api_router

__all__ = ["api_router"]

