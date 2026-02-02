"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest


@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Create a sample test video."""
    video_path = tmp_path / "test_video.mp4"

    # Create a simple test video with a moving rectangle (simulating a person)
    width, height = 640, 480
    fps = 30
    duration_seconds = 5
    total_frames = int(fps * duration_seconds)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for i in range(total_frames):
        # Create frame with gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = 100  # Blue channel
        frame[:, :, 1] = 150  # Green channel

        # Draw a moving rectangle (simulating a person)
        x = int(100 + (400 * i / total_frames))
        y = int(height // 2)
        cv2.rectangle(frame, (x - 30, y - 100), (x + 30, y + 100), (255, 200, 150), -1)

        writer.write(frame)

    writer.release()
    return video_path


@pytest.fixture
def short_video_path(tmp_path: Path) -> Path:
    """Create a video that's too short (1 second)."""
    video_path = tmp_path / "short_video.mp4"

    width, height = 640, 480
    fps = 30
    total_frames = 30  # 1 second

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for _ in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        writer.write(frame)

    writer.release()
    return video_path


@pytest.fixture
def low_res_video_path(tmp_path: Path) -> Path:
    """Create a video with low resolution."""
    video_path = tmp_path / "low_res_video.mp4"

    width, height = 320, 240  # Below 480p
    fps = 30
    total_frames = 150  # 5 seconds

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for _ in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        writer.write(frame)

    writer.release()
    return video_path


@pytest.fixture
def sample_pose_sequence():
    """Create a sample PoseSequence for testing."""
    from peakflow.models.schemas import PoseSequence, FramePose, PoseLandmark

    frames = []
    for i in range(30):  # 1 second at 30fps
        landmarks = []
        for j in range(33):  # 33 MediaPipe landmarks
            landmarks.append(
                PoseLandmark(
                    x=0.5 + 0.01 * np.sin(i / 10 + j / 5),
                    y=0.3 + j * 0.02,
                    z=0.0,
                    visibility=0.9,
                )
            )
        frames.append(
            FramePose(frame_idx=i, landmarks=landmarks, overall_confidence=0.9)
        )

    return PoseSequence(frames=frames, fps=30.0, total_duration_ms=1000.0)
