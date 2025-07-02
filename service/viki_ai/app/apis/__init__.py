from fastapi import APIRouter
from .lookup import router as lookup_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(lookup_router, tags=["Lookup Management"])

__all__ = ["api_router"]