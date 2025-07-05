from fastapi import APIRouter
from .lookup import router as lookup_router
from .fileStore import router as fileStore_router
from .llm import router as llm_router
from .tool import router as tool_router
from .knowledge import router as knowledge_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(lookup_router, tags=["Lookup Management"])
api_router.include_router(fileStore_router, tags=["File Store Management"])
api_router.include_router(llm_router, tags=["LLM Management"])
api_router.include_router(tool_router, tags=["Tool Management"])
api_router.include_router(knowledge_router, tags=["Knowledge Base Management"])

__all__ = ["api_router"]