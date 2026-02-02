"""Tests for Stage 1: Quality Gating."""

from pathlib import Path

import pytest

from peakflow.models.enums import RejectionReason
from peakflow.pipeline.stage1_gating import (
    extract_metadata,
    check_duration,
    check_resolution,
    check_fps,
    run_gating,
)


class TestExtractMetadata:
    """Tests for metadata extraction."""

    def test_extract_metadata_valid_video(self, sample_video_path: Path):
        """Test extracting metadata from a valid video."""
        metadata = extract_metadata(sample_video_path)

        assert metadata.path == str(sample_video_path)
        assert metadata.width == 640
        assert metadata.height == 480
        assert metadata.fps == 30.0
        assert 4.0 <= metadata.duration_seconds <= 6.0  # ~5 seconds
        assert metadata.total_frames > 0

    def test_extract_metadata_invalid_path(self):
        """Test extracting metadata from non-existent file."""
        with pytest.raises(ValueError, match="Cannot open video"):
            extract_metadata("/nonexistent/path/video.mp4")


class TestDurationCheck:
    """Tests for duration validation."""

    def test_valid_duration(self, sample_video_path: Path):
        """Test that valid duration passes."""
        metadata = extract_metadata(sample_video_path)
        assert check_duration(metadata) is None

    def test_too_short_duration(self, short_video_path: Path):
        """Test that short video is rejected."""
        metadata = extract_metadata(short_video_path)
        assert check_duration(metadata) == RejectionReason.TOO_SHORT


class TestResolutionCheck:
    """Tests for resolution validation."""

    def test_valid_resolution(self, sample_video_path: Path):
        """Test that valid resolution passes."""
        metadata = extract_metadata(sample_video_path)
        assert check_resolution(metadata) is None

    def test_low_resolution(self, low_res_video_path: Path):
        """Test that low resolution is rejected."""
        metadata = extract_metadata(low_res_video_path)
        assert check_resolution(metadata) == RejectionReason.LOW_RESOLUTION


class TestFpsCheck:
    """Tests for FPS validation."""

    def test_valid_fps(self, sample_video_path: Path):
        """Test that valid FPS passes."""
        metadata = extract_metadata(sample_video_path)
        assert check_fps(metadata) is None


class TestRunGating:
    """Tests for the full gating pipeline."""

    def test_valid_video_passes(self, sample_video_path: Path):
        """Test that a valid video passes all checks."""
        result = run_gating(sample_video_path)

        assert result.passed is True
        assert result.rejection_reason is None
        assert result.rejection_message is None
        assert result.metadata is not None

    def test_short_video_fails(self, short_video_path: Path):
        """Test that a short video fails."""
        result = run_gating(short_video_path)

        assert result.passed is False
        assert result.rejection_reason == RejectionReason.TOO_SHORT
        assert result.rejection_message is not None
        assert "at least" in result.rejection_message.lower()

    def test_low_res_video_fails(self, low_res_video_path: Path):
        """Test that a low resolution video fails."""
        result = run_gating(low_res_video_path)

        assert result.passed is False
        assert result.rejection_reason == RejectionReason.LOW_RESOLUTION

    def test_invalid_path_fails(self):
        """Test that invalid path returns failure."""
        result = run_gating("/nonexistent/path/video.mp4")

        assert result.passed is False
        assert "Cannot read video file" in result.rejection_message
