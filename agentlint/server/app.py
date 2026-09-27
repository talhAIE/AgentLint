"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="AgentLint UI API", version="0.1.0")

    # Allow frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .routers import scan, artifacts, demo
    app.include_router(scan.router)
    app.include_router(artifacts.router)
    app.include_router(demo.router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # Mount static files if they exist (for production build)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app
