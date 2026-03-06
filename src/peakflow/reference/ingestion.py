"""
Shared ingestion module for PeakFlow reference library.

Provides core functions for processing reference clips:
- Quality gating, pose extraction, embedding computation
- Auto-detection of stance/direction
- Manifest management
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from peakflow.config import settings
from peakflow.models.enums import Direction, Stance
from peakflow.models.schemas import PoseSequence
from peakflow.pipeline.stage1_gating import run_gating
from peakflow.pipeline.stage2_context import ContextDetector
from peakflow.pipeline.stage3_pose import PoseExtractor
from peakflow.pipeline.stage4_matching import ReferenceMatcher

logger = logging.getLogger(__name__)

# Maneuver abbreviations for clip IDs
MANEUVER_ABBREV = {
    "bottom_turn": "bt",
    "cutback": "cb",
    "top_turn": "tt",
}

DEFAULT_MANIFEST = {
    "version": "1.0",
    "clips": [],
}


@dataclass
class IngestionResult:
    """Result of processing a single reference clip."""

    success: bool
    clip_id: Optional[str] = None
    error_message: Optional[str] = None
    pose_quality_score: Optional[float] = None
    auto_detected_stance: Optional[str] = None
    auto_detected_direction: Optional[str] = None
    detection_confidence: Optional[float] = None
    frame_count: Optional[int] = None
    fps: Optional[float] = None


def ensure_directories(reference_dir: Path) -> None:
    """Create reference directories if they don't exist."""
    for subdir in ["clips", "poses", "embeddings"]:
        (reference_dir / subdir).mkdir(parents=True, exist_ok=True)


def load_manifest(reference_dir: Path) -> dict:
    """Load manifest.json or create default if not exists."""
    manifest_path = reference_dir / "manifest.json"

    if not manifest_path.exists():
        save_manifest(reference_dir, DEFAULT_MANIFEST)
        return DEFAULT_MANIFEST.copy()

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Migrate old format if needed
    if "references" in manifest and "clips" not in manifest:
        manifest["clips"] = manifest.pop("references")
        save_manifest(reference_dir, manifest)

    return manifest


def save_manifest(reference_dir: Path, manifest: dict) -> None:
    """Save manifest.json with proper formatting."""
    manifest_path = reference_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def generate_clip_id(
    manifest: dict,
    maneuver: str,
    stance: str,
    direction: str,
    style_tags: list[str],
) -> str:
    """Generate unique clip ID: {maneuver}_{stance}_{direction}_{style}_{counter:03d}"""
    maneuver_abbr = MANEUVER_ABBREV.get(maneuver, maneuver[:2])
    stance_abbr = stance[:3] if stance != "regular" else "regular"
    direction_abbr = "fs" if direction == "frontside" else "bs"
    style_abbr = style_tags[0] if style_tags else "default"

    prefix = f"{maneuver_abbr}_{stance_abbr}_{direction_abbr}_{style_abbr}_"
    existing_ids = [c["clip_id"] for c in manifest.get("clips", [])]

    counter = 1
    while f"{prefix}{counter:03d}" in existing_ids:
        counter += 1

    return f"{prefix}{counter:03d}"


def pose_sequence_to_numpy(pose_sequence: PoseSequence) -> np.ndarray:
    """Convert PoseSequence to numpy array of shape (T, 33, 4)."""
    frames_data = []
    for frame in pose_sequence.frames:
        landmarks_data = []
        for lm in frame.landmarks:
            landmarks_data.append([lm.x, lm.y, lm.z, lm.visibility])
        frames_data.append(landmarks_data)
    return np.array(frames_data, dtype=np.float32)


def compute_pose_quality_score(pose_sequence: PoseSequence) -> float:
    """
    Compute a quality score (0-1) for extracted pose data.
    Based on: average confidence, valid frame ratio, trajectory smoothness.
    """
    if not pose_sequence.frames:
        return 0.0

    # Average confidence across all frames
    confidences = [f.overall_confidence for f in pose_sequence.frames]
    avg_confidence = sum(confidences) / len(confidences)

    # Proportion of high-confidence frames (>0.5)
    high_conf_frames = sum(1 for c in confidences if c > 0.5)
    valid_ratio = high_conf_frames / len(confidences)

    # Trajectory smoothness: measure jitter in hip position
    if len(pose_sequence.frames) >= 3:
        hip_positions = []
        for frame in pose_sequence.frames:
            lm = frame.landmarks
            hip_x = (lm[23].x + lm[24].x) / 2
            hip_y = (lm[23].y + lm[24].y) / 2
            hip_positions.append((hip_x, hip_y))

        # Compute acceleration (second derivative)
        accelerations = []
        for i in range(1, len(hip_positions) - 1):
            ax = hip_positions[i + 1][0] - 2 * hip_positions[i][0] + hip_positions[i - 1][0]
            ay = hip_positions[i + 1][1] - 2 * hip_positions[i][1] + hip_positions[i - 1][1]
            accelerations.append((ax**2 + ay**2) ** 0.5)

        avg_accel = sum(accelerations) / len(accelerations) if accelerations else 0
        # Lower acceleration = smoother = better. Normalize: 0.01 threshold
        smoothness = max(0.0, 1.0 - avg_accel * 50)
    else:
        smoothness = 0.5

    # Weighted combination
    score = 0.4 * avg_confidence + 0.3 * valid_ratio + 0.3 * smoothness
    return round(min(1.0, max(0.0, score)), 3)


def process_single_clip(
    video_path: Path,
    maneuver: str,
    surfer_name: str,
    source: str,
    quality: int,
    style_tags: list[str],
    reference_dir: Path,
    stance: Optional[str] = None,
    direction: Optional[str] = None,
    pose_extractor: Optional[PoseExtractor] = None,
    context_detector: Optional[ContextDetector] = None,
    min_pose_quality: float = 0.6,
    min_detection_confidence: float = 0.7,
) -> IngestionResult:
    """
    Process a single clip through the full reference pipeline.
    Auto-detects stance/direction if not provided.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        return IngestionResult(success=False, error_message=f"Video not found: {video_path}")

    ensure_directories(reference_dir)

    # Step 1: Quality gating
    logger.info(f"[1/5] Gating: {video_path.name}")
    gating_result = run_gating(str(video_path))
    if not gating_result.passed:
        return IngestionResult(
            success=False,
            error_message=f"Gating failed: {gating_result.rejection_message}",
        )

    # Step 2: Pose extraction
    logger.info(f"[2/5] Extracting poses: {video_path.name}")
    try:
        extractor = pose_extractor or PoseExtractor()
        pose_sequence, rejection_reason = extractor.process_video(str(video_path))
        if pose_sequence is None:
            reason = rejection_reason.value if rejection_reason else "Unknown"
            return IngestionResult(success=False, error_message=f"Pose extraction failed: {reason}")
    except Exception as e:
        return IngestionResult(success=False, error_message=f"Pose extraction error: {e}")

    # Quality check
    pose_quality = compute_pose_quality_score(pose_sequence)
    if pose_quality < min_pose_quality:
        logger.warning(f"Low pose quality ({pose_quality:.2f}) for {video_path.name}")

    # Step 3: Auto-detect stance/direction if not provided
    detected_stance = stance
    detected_direction = direction
    detection_confidence = None

    if not stance or not direction:
        logger.info(f"[3/5] Auto-detecting context: {video_path.name}")
        detector = context_detector or ContextDetector()
        context = detector.detect(pose_sequence)
        detection_confidence = context.confidence

        if not stance:
            if context.confidence >= min_detection_confidence:
                detected_stance = context.stance.value
                logger.info(f"  Auto-detected stance: {detected_stance} (conf: {context.confidence:.2f})")
            else:
                detected_stance = "unknown"
                logger.warning(f"  Low stance confidence ({context.confidence:.2f}), set to unknown")

        if not direction:
            if context.confidence >= min_detection_confidence:
                detected_direction = context.direction.value
                logger.info(f"  Auto-detected direction: {detected_direction} (conf: {context.confidence:.2f})")
            else:
                detected_direction = "unknown"
                logger.warning(f"  Low direction confidence ({context.confidence:.2f}), set to unknown")
    else:
        logger.info(f"[3/5] Using provided context: stance={stance}, direction={direction}")

    # Step 4: Generate clip ID and save artifacts
    logger.info(f"[4/5] Computing embedding: {video_path.name}")
    manifest = load_manifest(reference_dir)
    clip_id = generate_clip_id(manifest, maneuver, detected_stance, detected_direction, style_tags)

    # Copy video
    video_ext = video_path.suffix.lower()
    dest_video = reference_dir / "clips" / f"{clip_id}{video_ext}"
    shutil.copy2(video_path, dest_video)

    # Save poses
    pose_array = pose_sequence_to_numpy(pose_sequence)
    pose_file = f"{clip_id}.npy"
    np.save(reference_dir / "poses" / pose_file, pose_array)

    # Compute and save embedding
    try:
        matcher = ReferenceMatcher(reference_dir)
        embedding = matcher.compute_embedding(pose_sequence)
        embedding_file = f"{clip_id}.npy"
        np.save(reference_dir / "embeddings" / embedding_file, embedding)
    except Exception as e:
        # Clean up on failure
        dest_video.unlink(missing_ok=True)
        (reference_dir / "poses" / pose_file).unlink(missing_ok=True)
        return IngestionResult(success=False, error_message=f"Embedding error: {e}")

    # Step 5: Update manifest
    logger.info(f"[5/5] Updating manifest: {clip_id}")
    clip_entry = {
        "clip_id": clip_id,
        "maneuver": maneuver,
        "stance": detected_stance,
        "direction": detected_direction,
        "style_tags": style_tags,
        "surfer_name": surfer_name,
        "source": source,
        "camera_angle": "lateral_beach",
        "quality_score": quality,
        "pose_file": f"poses/{pose_file}",
        "embedding_file": f"embeddings/{embedding_file}",
        "video_file": f"clips/{clip_id}{video_ext}",
        "frame_count": len(pose_sequence.frames),
        "fps": pose_sequence.fps,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest["clips"].append(clip_entry)
    save_manifest(reference_dir, manifest)

    logger.info(f"Successfully added: {clip_id}")

    return IngestionResult(
        success=True,
        clip_id=clip_id,
        pose_quality_score=pose_quality,
        auto_detected_stance=detected_stance,
        auto_detected_direction=detected_direction,
        detection_confidence=detection_confidence,
        frame_count=len(pose_sequence.frames),
        fps=pose_sequence.fps,
    )
