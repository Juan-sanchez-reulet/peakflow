"""Pydantic models for PeakFlow pipeline data structures."""

from typing import Optional

from pydantic import BaseModel

from peakflow.models.enums import (
    Stance,
    Direction,
    ManeuverType,
    Phase,
    RejectionReason,
)


# -------------------------------------------------------------------
# Stage 1: Gating
# -------------------------------------------------------------------
class VideoMetadata(BaseModel):
    """Metadata extracted from a video file."""

    path: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    total_frames: int


class GatingResult(BaseModel):
    """Result of the quality gating stage."""

    passed: bool
    rejection_reason: Optional[RejectionReason] = None
    rejection_message: Optional[str] = None
    metadata: Optional[VideoMetadata] = None


# -------------------------------------------------------------------
# Stage 2: Context
# -------------------------------------------------------------------
class ContextResult(BaseModel):
    """Detected context for the surf maneuver."""

    stance: Stance
    direction: Direction
    wave_direction: str  # "left_to_right" or "right_to_left"
    confidence: float


# -------------------------------------------------------------------
# Stage 3: Pose
# -------------------------------------------------------------------
class BoundingBox(BaseModel):
    """Bounding box for person detection."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    frame_idx: int


class PoseLandmark(BaseModel):
    """Single landmark with 3D coordinates + visibility."""

    x: float
    y: float
    z: float
    visibility: float


class FramePose(BaseModel):
    """Pose for a single frame."""

    frame_idx: int
    landmarks: list[PoseLandmark]  # 33 MediaPipe landmarks
    overall_confidence: float


class PoseSequence(BaseModel):
    """Full pose sequence for a video."""

    frames: list[FramePose]
    fps: float
    total_duration_ms: float

    model_config = {"arbitrary_types_allowed": True}


# -------------------------------------------------------------------
# Stage 4: Matching
# -------------------------------------------------------------------
class ReferenceClip(BaseModel):
    """Reference clip metadata from the pro library."""

    clip_id: str
    maneuver: ManeuverType
    stance: Stance
    direction: Direction
    style_tags: list[str]
    surfer_name: str
    source: str
    camera_angle: str
    quality_score: int
    pose_file: str
    embedding_file: str


class MatchResult(BaseModel):
    """Result of reference matching stage."""

    matched_references: list[ReferenceClip]
    style_cluster: str
    similarity_scores: list[float]


# -------------------------------------------------------------------
# Stage 5: DTW
# -------------------------------------------------------------------
class JointDeviation(BaseModel):
    """Deviation metrics for a single joint/feature."""

    joint_name: str
    mean_deviation: float
    max_deviation: float
    max_deviation_frame: int
    max_deviation_phase: Phase


class AlignmentResult(BaseModel):
    """Result of DTW alignment."""

    path: list[tuple[int, int]]  # (user_frame, pro_frame) pairs
    total_cost: float
    normalized_cost: float


class DeviationAnalysis(BaseModel):
    """Full deviation analysis from DTW alignment."""

    primary_error: str
    primary_error_description: str
    severity: float  # 0-1 scale
    phase: Phase
    timing_offset_ms: float
    joint_deviations: list[JointDeviation]
    alignment: AlignmentResult


# -------------------------------------------------------------------
# Stage 6: Feedback
# -------------------------------------------------------------------
class FeedbackResult(BaseModel):
    """Generated coaching feedback."""

    what_you_are_doing: str
    what_to_fix: str
    why_it_matters: str
    dry_land_drill: str
    in_water_cue: str
    pro_insight: str
    overlay_video_path: Optional[str] = None


# -------------------------------------------------------------------
# Full Pipeline Output
# -------------------------------------------------------------------
class AnalysisResult(BaseModel):
    """Complete analysis result from the pipeline."""

    video_path: str
    gating: GatingResult
    context: Optional[ContextResult] = None
    pose_sequence: Optional[PoseSequence] = None
    match: Optional[MatchResult] = None
    deviation: Optional[DeviationAnalysis] = None
    feedback: Optional[FeedbackResult] = None
    processing_time_ms: float
