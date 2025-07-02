import pyfiglet
import uvicorn
from fastapi import FastAPI, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from .app.utils.config import settings
from .app.utils import flyway
from .app.utils import proxy
from .app.utils.database import create_db_engine
from .app.apis import api_router

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    app = FastAPI(
        title="VIKI AI API",
        description="The AI Agent platform for intelligent actions!",
        version=settings.VERSION,
        docs_url=f"/api/v{settings.VERSION}/docs",
        redoc_url=f"/api/v{settings.VERSION}/redoc",
        openapi_url=f"/api/v{settings.VERSION}/openapi.json"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.VERSION}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to VIKI AI - The AI Agent platform for intelligent actions!",
            "version": settings.VERSION,
            "docs": f"/api/v{settings.VERSION}/docs"
        }

    return app


def main():
    """
    Entry point for the VIKI AI.
    This is a FastAPI application that serves as a wrapper for the VIKI AI API.
    """

    # Print the welcome message
    print(pyfiglet.figlet_format("VIKI AI").rstrip())
    print("The AI Agent platform for intelligent actions!\n")

    # Update proxy configuration
    proxy.update_proxy_config()

    # Create DB
    flyway.create_sqlite_db()
    flyway.update_flyway_config()
    flyway.run_flyway_migrations()

    # Initialize database engine
    create_db_engine()

    # Create FastAPI app
    app = create_app()

    # Start the FastAPI server
    settings.logger.info(f"Starting VIKI AI server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()