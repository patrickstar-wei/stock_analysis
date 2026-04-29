from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.config import settings
from app.job_manager import JobManager


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.job_manager = JobManager(settings)
    app.include_router(router)

    static_dir = Path(__file__).resolve().parents[1] / "static"

    @app.get("/")
    def root():
        if (static_dir / "index.html").exists():
            return FileResponse(static_dir / "index.html")
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api_prefix": "/api/v1",
        }

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_app()
