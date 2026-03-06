"""Settings & constants for PeakFlow pipeline."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    REFERENCE_DIR: Path = DATA_DIR / "references"

    # Video constraints (Stage 1)
    MIN_DURATION_SEC: float = 3.0
    MAX_DURATION_SEC: float = 15.0
    MIN_RESOLUTION: int = 480
    MIN_FPS: float = 24.0

    # Tracking (Stage 3)
    YOLO_MODEL: str = str(Path(__file__).parent.parent.parent / "yolov8n.pt")
    YOLO_CONFIDENCE: float = 0.3
    TRACKING_MAX_AGE: int = 30
    BBOX_PADDING_RATIO: float = 0.2

    # Pose (Stage 3)
    POSE_MIN_CONFIDENCE: float = 0.5
    POSE_SMOOTHING_WINDOW: int = 5
    MAX_JOINT_SPEED_M_S: float = 5.0

    # Camera angle detection thresholds
    SHOULDER_HIP_RATIO_HEAD_ON: float = 2.0
    SHOULDER_HIP_RATIO_FROM_BEHIND: float = 0.5

    # DTW (Stage 5)
    DTW_FEATURES: list[str] = [
        "knee_flexion_back",
        "knee_flexion_front",
        "hip_flexion",
        "torso_lean",
        "arm_elevation_leading",
        "arm_elevation_trailing",
        "compression_index",
    ]

    # Attention weights (learnable, but start with these)
    DTW_ATTENTION_WEIGHTS: dict[str, float] = {
        "knee_flexion_back": 1.0,
        "knee_flexion_front": 0.8,
        "hip_flexion": 0.9,
        "torso_lean": 0.7,
        "arm_elevation_leading": 0.5,
        "arm_elevation_trailing": 0.5,
        "compression_index": 1.0,
    }

    # Reference matching (Stage 4)
    TOP_K_REFERENCES: int = 3

    # LLM (Stage 6)
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_MAX_TOKENS: int = 1024

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    MAX_UPLOAD_SIZE_MB: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
