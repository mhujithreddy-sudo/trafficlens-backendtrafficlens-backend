"""
TrafficLens Application Runner.
Executes the FastAPI application using Uvicorn.
"""

import uvicorn
from app.core.config import settings
from app.core.logging_config import logger

if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_dirs=["app"] if settings.DEBUG else None,
        reload_excludes=["*.db*", "*.db-journal", "*.log"] if settings.DEBUG else None,
        log_level="info" if not settings.DEBUG else "debug",
    )
