"""Enums for PeakFlow pipeline."""

from enum import Enum


class Stance(str, Enum):
    """Surfer's stance on the board."""

    REGULAR = "regular"  # Left foot forward
    GOOFY = "goofy"  # Right foot forward
    UNKNOWN = "unknown"


class Direction(str, Enum):
    """Direction of the turn relative to the wave."""

    FRONTSIDE = "frontside"  # Facing the wave
    BACKSIDE = "backside"  # Back to the wave
    UNKNOWN = "unknown"


class ManeuverType(str, Enum):
    """Type of surf maneuver being analyzed."""

    BOTTOM_TURN = "bottom_turn"
    CUTBACK = "cutback"
    TOP_TURN = "top_turn"


class Phase(str, Enum):
    """Phase of the maneuver."""

    ENTRY = "entry"
    LOADING = "loading"
    DRIVE = "drive"
    EXIT = "exit"


class RejectionReason(str, Enum):
    """Reasons for rejecting a video at the gating stage."""

    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    LOW_RESOLUTION = "low_resolution"
    LOW_FPS = "low_fps"
    NO_PERSON = "no_person"
    MULTIPLE_PEOPLE = "multiple_people"
    HEAD_ON_ANGLE = "head_on_angle"
    FROM_BEHIND_ANGLE = "from_behind_angle"
    LOW_POSE_CONFIDENCE = "low_pose_confidence"
