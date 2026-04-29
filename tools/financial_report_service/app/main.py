from __future__ import annotations

from fastapi import FastAPI

from app.api import router
from app.config import settings
from app.job_manager import JobManager


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.job_manager = JobManager(settings)
    app.include_router(router)

    @app.get("/")
    def root() -> dict:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api_prefix": "/api/v1",
        }

    return app


app = create_app()
