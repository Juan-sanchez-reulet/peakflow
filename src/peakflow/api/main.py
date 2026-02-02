"""FastAPI application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
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
        reload=True,
    )


if __name__ == "__main__":
    run()
