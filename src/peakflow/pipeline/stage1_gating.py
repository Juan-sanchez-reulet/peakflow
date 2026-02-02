"""
Stage 1: Quality Gating
Reject videos that will produce bad analysis BEFORE processing.
"""

from pathlib import Path

import cv2

from peakflow.config import settings
from peakflow.models.schemas import GatingResult, VideoMetadata, RejectionReason


REJECTION_MESSAGES = {
    RejectionReason.TOO_SHORT: (
        f"Video must be at least {settings.MIN_DURATION_SEC} seconds. "
        "Please record a longer clip that captures the full maneuver."
    ),
    RejectionReason.TOO_LONG: (
        f"Video must be under {settings.MAX_DURATION_SEC} seconds. "
        "Please trim to just the maneuver you want analyzed."
    ),
    RejectionReason.LOW_RESOLUTION: (
        f"Video resolution must be at least {settings.MIN_RESOLUTION}p. "
        "Please record in higher quality for accurate pose detection."
    ),
    RejectionReason.LOW_FPS: (
        f"Video must be at least {settings.MIN_FPS} fps. "
        "Please record at a higher frame rate to capture the motion."
    ),
    RejectionReason.NO_PERSON: (
        "No surfer detected in the video. "
        "Please ensure the surfer is clearly visible throughout the clip."
    ),
    RejectionReason.MULTIPLE_PEOPLE: (
        "Multiple people detected. "
        "Please record a clip with only one surfer visible."
    ),
    RejectionReason.HEAD_ON_ANGLE: (
        "Camera angle is too head-on. "
        "Please record from the side of the surfer (perpendicular to the wave), "
        "standing on the beach about 20-50 meters away."
    ),
    RejectionReason.FROM_BEHIND_ANGLE: (
        "Camera angle is from behind the surfer. "
        "Please record from the side (lateral view) for accurate analysis."
    ),
    RejectionReason.LOW_POSE_CONFIDENCE: (
        "Could not reliably detect the surfer's pose. "
        "Please ensure good lighting and that the surfer is clearly visible."
    ),
}


def extract_metadata(video_path: str | Path) -> VideoMetadata:
    """Extract video metadata using OpenCV."""
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    cap.release()

    return VideoMetadata(
        path=str(video_path),
        duration_seconds=duration,
        width=width,
        height=height,
        fps=fps,
        total_frames=total_frames,
    )


def check_duration(metadata: VideoMetadata) -> RejectionReason | None:
    """Check if duration is within bounds."""
    if metadata.duration_seconds < settings.MIN_DURATION_SEC:
        return RejectionReason.TOO_SHORT
    if metadata.duration_seconds > settings.MAX_DURATION_SEC:
        return RejectionReason.TOO_LONG
    return None


def check_resolution(metadata: VideoMetadata) -> RejectionReason | None:
    """Check if resolution meets minimum."""
    min_dim = min(metadata.width, metadata.height)
    if min_dim < settings.MIN_RESOLUTION:
        return RejectionReason.LOW_RESOLUTION
    return None


def check_fps(metadata: VideoMetadata) -> RejectionReason | None:
    """Check if FPS meets minimum."""
    if metadata.fps < settings.MIN_FPS:
        return RejectionReason.LOW_FPS
    return None


def run_gating(video_path: str | Path) -> GatingResult:
    """
    Run all gating checks in order.
    Returns as soon as a check fails.
    """
    # Extract metadata
    try:
        metadata = extract_metadata(video_path)
    except Exception as e:
        return GatingResult(
            passed=False,
            rejection_reason=None,
            rejection_message=f"Cannot read video file: {e}",
        )

    # Run checks in order (cheapest first)
    checks = [
        check_duration,
        check_resolution,
        check_fps,
    ]

    for check_fn in checks:
        rejection = check_fn(metadata)
        if rejection:
            return GatingResult(
                passed=False,
                rejection_reason=rejection,
                rejection_message=REJECTION_MESSAGES[rejection],
                metadata=metadata,
            )

    # All checks passed
    return GatingResult(passed=True, metadata=metadata)


def get_rejection_message(reason: RejectionReason) -> str:
    """Get the user-friendly rejection message for a reason."""
    return REJECTION_MESSAGES.get(reason, "Video rejected for unknown reason.")
