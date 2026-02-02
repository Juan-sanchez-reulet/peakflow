"""FastAPI routes for the analysis API."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from peakflow.api.dependencies import get_orchestrator
from peakflow.config import settings
from peakflow.models.schemas import AnalysisResult, GatingResult
from peakflow.pipeline.orchestrator import PipelineOrchestrator


router = APIRouter()


ALLOWED_CONTENT_TYPES = [
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
]


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_video(
    video: UploadFile = File(...),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
) -> AnalysisResult:
    """
    Analyze a surf video and return coaching feedback.

    Accepts: MP4, MOV, AVI, WebM (3-15 seconds, >=480p, >=24fps)
    Returns: Analysis result with feedback or rejection reason
    """
    # Validate file type
    if video.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{video.content_type}'. "
            f"Allowed: {ALLOWED_CONTENT_TYPES}",
        )

    # Check file size
    video.file.seek(0, 2)  # Seek to end
    file_size = video.file.tell()
    video.file.seek(0)  # Seek back to start

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # Determine file extension
    extension = ".mp4"  # Default
    if video.filename:
        ext = Path(video.filename).suffix.lower()
        if ext in [".mp4", ".mov", ".avi", ".webm"]:
            extension = ext

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        # Run analysis
        result = orchestrator.analyze(tmp_path)
        return result

    finally:
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/validate", response_model=GatingResult)
async def validate_video(
    video: UploadFile = File(...),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
) -> GatingResult:
    """
    Quick validation of a video without full analysis.

    Returns gating result with pass/fail and reason.
    Useful for client-side validation before upload.
    """
    # Validate file type
    if video.content_type not in ALLOWED_CONTENT_TYPES:
        return GatingResult(
            passed=False,
            rejection_message=f"Invalid file type '{video.content_type}'.",
        )

    # Determine file extension
    extension = ".mp4"
    if video.filename:
        ext = Path(video.filename).suffix.lower()
        if ext in [".mp4", ".mov", ".avi", ".webm"]:
            extension = ext

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        # Run quick analysis
        result = orchestrator.analyze_quick(tmp_path)
        return result.gating

    finally:
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@router.get("/config")
async def get_config() -> dict:
    """Get current configuration (non-sensitive values only)."""
    return {
        "min_duration_sec": settings.MIN_DURATION_SEC,
        "max_duration_sec": settings.MAX_DURATION_SEC,
        "min_resolution": settings.MIN_RESOLUTION,
        "min_fps": settings.MIN_FPS,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
    }
