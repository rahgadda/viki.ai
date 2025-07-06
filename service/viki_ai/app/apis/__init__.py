from fastapi import APIRouter
from .lookup import router as lookup_router
from .fileStore import router as fileStore_router
from .llm import router as llm_router
from .agent import router as agent_router
from .tool import router as tool_router
from .knowledge import router as knowledge_router
from .chat import router as chat_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(lookup_router, tags=["Lookup Management"])
api_router.include_router(fileStore_router, tags=["File Store Management"])
api_router.include_router(llm_router, tags=["LLM Management"])
api_router.include_router(agent_router, tags=["Agent Management"])
api_router.include_router(tool_router, tags=["Tool Management"])
api_router.include_router(knowledge_router, tags=["Knowledge Base Management"])
api_router.include_router(chat_router, tags=["Chat Management"])

__all__ = ["api_router"]