"""FastAPI application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from peakflow.api.routes import router
from peakflow.config import settings


app = FastAPI(
    title="PeakFlow API",
    description="Surf video analysis engine with AI-powered coaching feedback",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["analysis"])

# Serve frontend static files
FRONTEND_DIST = settings.BASE_DIR / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def root():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """SPA fallback — all non-API routes serve index.html."""
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": "PeakFlow API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }


def run():
    """Run the API server."""
    uvicorn.run(
        "peakflow.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
    )


if __name__ == "__main__":
    run()
