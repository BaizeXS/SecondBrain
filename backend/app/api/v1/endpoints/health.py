"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "Second Brain Backend",
        "version": "1.0.0"
    }