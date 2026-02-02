"""
Stage 5: DTW Alignment + Metrics
Attention-weighted Dynamic Time Warping for sequence alignment.
"""

import numpy as np

from peakflow.config import settings
from peakflow.models.schemas import (
    PoseSequence,
    AlignmentResult,
    DeviationAnalysis,
    JointDeviation,
    Phase,
)


# MediaPipe landmark indices
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16


def compute_joint_angles(landmarks: list) -> dict[str, float]:
    """
    Compute joint angles from pose landmarks.
    Returns view-invariant features (angles don't depend on camera position).
    """

    def get_xyz(idx):
        return np.array([landmarks[idx].x, landmarks[idx].y, landmarks[idx].z])

    def angle_3points(a, b, c):
        """Angle at point b formed by points a-b-c."""
        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

    # Knee flexion (180 = straight, smaller = more bent)
    left_knee_angle = angle_3points(
        get_xyz(LEFT_HIP), get_xyz(LEFT_KNEE), get_xyz(LEFT_ANKLE)
    )
    right_knee_angle = angle_3points(
        get_xyz(RIGHT_HIP), get_xyz(RIGHT_KNEE), get_xyz(RIGHT_ANKLE)
    )

    # Hip flexion
    left_hip_angle = angle_3points(
        get_xyz(LEFT_SHOULDER), get_xyz(LEFT_HIP), get_xyz(LEFT_KNEE)
    )
    right_hip_angle = angle_3points(
        get_xyz(RIGHT_SHOULDER), get_xyz(RIGHT_HIP), get_xyz(RIGHT_KNEE)
    )

    # Torso lean (relative to vertical)
    hip_center = (get_xyz(LEFT_HIP) + get_xyz(RIGHT_HIP)) / 2
    shoulder_center = (get_xyz(LEFT_SHOULDER) + get_xyz(RIGHT_SHOULDER)) / 2
    torso_vec = shoulder_center - hip_center
    vertical = np.array([0, -1, 0])  # Y points down in image coords
    torso_lean = np.degrees(
        np.arccos(
            np.clip(np.dot(torso_vec, vertical) / (np.linalg.norm(torso_vec) + 1e-8), -1, 1)
        )
    )

    # Compression index (hip height relative to stance width)
    hip_y = (landmarks[LEFT_HIP].y + landmarks[RIGHT_HIP].y) / 2
    ankle_y = (landmarks[LEFT_ANKLE].y + landmarks[RIGHT_ANKLE].y) / 2
    compression = hip_y - ankle_y  # Smaller = more compressed

    # Arm elevation
    left_arm_angle = angle_3points(
        get_xyz(LEFT_HIP), get_xyz(LEFT_SHOULDER), get_xyz(LEFT_ELBOW)
    )
    right_arm_angle = angle_3points(
        get_xyz(RIGHT_HIP), get_xyz(RIGHT_SHOULDER), get_xyz(RIGHT_ELBOW)
    )

    return {
        "knee_flexion_left": left_knee_angle,
        "knee_flexion_right": right_knee_angle,
        "hip_flexion_left": left_hip_angle,
        "hip_flexion_right": right_hip_angle,
        "torso_lean": torso_lean,
        "compression_index": compression,
        "arm_elevation_left": left_arm_angle,
        "arm_elevation_right": right_arm_angle,
    }


def extract_feature_sequence(pose_sequence: PoseSequence, stance: str) -> np.ndarray:
    """
    Extract feature sequence from pose sequence.
    Maps left/right to front/back based on stance.
    """
    features = []

    for frame in pose_sequence.frames:
        angles = compute_joint_angles(frame.landmarks)

        # Map to front/back based on stance
        if stance == "regular":
            # Left foot forward
            feature_vec = [
                angles["knee_flexion_right"],  # back knee
                angles["knee_flexion_left"],  # front knee
                angles["hip_flexion_right"],  # hip
                angles["torso_lean"],
                angles["arm_elevation_right"],  # trailing arm
                angles["arm_elevation_left"],  # leading arm
                angles["compression_index"],
            ]
        else:  # goofy
            # Right foot forward
            feature_vec = [
                angles["knee_flexion_left"],  # back knee
                angles["knee_flexion_right"],  # front knee
                angles["hip_flexion_left"],  # hip
                angles["torso_lean"],
                angles["arm_elevation_left"],  # trailing arm
                angles["arm_elevation_right"],  # leading arm
                angles["compression_index"],
            ]

        features.append(feature_vec)

    return np.array(features)


def attention_weighted_distance(
    user_frame: np.ndarray, pro_frame: np.ndarray, weights: np.ndarray
) -> float:
    """Weighted Euclidean distance between feature vectors."""
    diff = user_frame - pro_frame
    weighted_diff = diff * weights
    return np.sqrt(np.sum(weighted_diff**2))


def dtw_align(
    user_seq: np.ndarray,
    pro_seq: np.ndarray,
    weights: np.ndarray | None = None,
) -> AlignmentResult:
    """
    Attention-weighted Dynamic Time Warping.

    Args:
        user_seq: User feature sequence (T1, D)
        pro_seq: Pro feature sequence (T2, D)
        weights: Feature importance weights (D,)

    Returns:
        AlignmentResult with path and costs
    """
    T1, D = user_seq.shape
    T2 = pro_seq.shape[0]

    if weights is None:
        weights = np.ones(D)

    # Cost matrix
    cost = np.zeros((T1, T2))
    for i in range(T1):
        for j in range(T2):
            cost[i, j] = attention_weighted_distance(user_seq[i], pro_seq[j], weights)

    # Cumulative cost matrix (DTW)
    cum_cost = np.full((T1 + 1, T2 + 1), np.inf)
    cum_cost[0, 0] = 0

    for i in range(1, T1 + 1):
        for j in range(1, T2 + 1):
            cum_cost[i, j] = cost[i - 1, j - 1] + min(
                cum_cost[i - 1, j],  # insertion
                cum_cost[i, j - 1],  # deletion
                cum_cost[i - 1, j - 1],  # match
            )

    # Backtrack to get alignment path
    path = []
    i, j = T1, T2
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))

        candidates = [
            (cum_cost[i - 1, j], (i - 1, j)),
            (cum_cost[i, j - 1], (i, j - 1)),
            (cum_cost[i - 1, j - 1], (i - 1, j - 1)),
        ]
        _, (i, j) = min(candidates, key=lambda x: x[0])

    path.reverse()

    total_cost = cum_cost[T1, T2]
    normalized_cost = total_cost / len(path) if path else 0

    return AlignmentResult(
        path=path,
        total_cost=float(total_cost),
        normalized_cost=float(normalized_cost),
    )


def get_attention_weights() -> np.ndarray:
    """Get attention weights for DTW features."""
    feature_names = [
        "knee_flexion_back",
        "knee_flexion_front",
        "hip_flexion",
        "torso_lean",
        "arm_elevation_trailing",
        "arm_elevation_leading",
        "compression_index",
    ]

    return np.array(
        [settings.DTW_ATTENTION_WEIGHTS.get(name, 1.0) for name in feature_names]
    )


def compute_deviations(
    user_seq: np.ndarray,
    pro_seq: np.ndarray,
    alignment: AlignmentResult,
    fps: float,
) -> DeviationAnalysis:
    """
    Compute per-joint deviations after alignment.
    """
    feature_names = [
        "knee_flexion_back",
        "knee_flexion_front",
        "hip_flexion",
        "torso_lean",
        "arm_elevation_trailing",
        "arm_elevation_leading",
        "compression_index",
    ]

    # Compute deviations for each feature
    joint_deviations = []

    for feat_idx, feat_name in enumerate(feature_names):
        deviations = []
        for user_idx, pro_idx in alignment.path:
            dev = user_seq[user_idx, feat_idx] - pro_seq[pro_idx, feat_idx]
            deviations.append(dev)

        deviations = np.array(deviations)
        max_idx = np.argmax(np.abs(deviations))

        # Determine phase based on position in sequence
        relative_pos = max_idx / len(deviations)
        if relative_pos < 0.25:
            phase = Phase.ENTRY
        elif relative_pos < 0.5:
            phase = Phase.LOADING
        elif relative_pos < 0.75:
            phase = Phase.DRIVE
        else:
            phase = Phase.EXIT

        joint_deviations.append(
            JointDeviation(
                joint_name=feat_name,
                mean_deviation=float(np.mean(deviations)),
                max_deviation=float(np.max(np.abs(deviations))),
                max_deviation_frame=int(max_idx),
                max_deviation_phase=phase,
            )
        )

    # Find primary error (largest weighted deviation)
    weights = get_attention_weights()

    weighted_max_devs = [
        jd.max_deviation * weights[i] for i, jd in enumerate(joint_deviations)
    ]
    primary_idx = np.argmax(weighted_max_devs)
    primary_error = joint_deviations[primary_idx]

    # Compute timing offset
    # Find where user is vs where pro is at peak deviation
    if alignment.path:
        user_frame, pro_frame = alignment.path[primary_error.max_deviation_frame]
        timing_offset_ms = ((user_frame - pro_frame) / fps) * 1000
    else:
        timing_offset_ms = 0.0

    # Generate description
    description = _generate_error_description(primary_error)

    return DeviationAnalysis(
        primary_error=primary_error.joint_name,
        primary_error_description=description,
        severity=min(1.0, primary_error.max_deviation / 30.0),  # Normalize to 0-1
        phase=primary_error.max_deviation_phase,
        timing_offset_ms=timing_offset_ms,
        joint_deviations=joint_deviations,
        alignment=alignment,
    )


def _generate_error_description(deviation: JointDeviation) -> str:
    """Generate human-readable description of the error."""
    joint_descriptions = {
        "knee_flexion_back": "back knee",
        "knee_flexion_front": "front knee",
        "hip_flexion": "hip angle",
        "torso_lean": "torso lean",
        "arm_elevation_trailing": "trailing arm position",
        "arm_elevation_leading": "leading arm position",
        "compression_index": "compression/stance",
    }

    joint_name = joint_descriptions.get(deviation.joint_name, deviation.joint_name)
    direction = "over-extended" if deviation.mean_deviation > 0 else "under-extended"

    return (
        f"{joint_name.capitalize()} deviation of {deviation.max_deviation:.1f}° "
        f"({direction}) during {deviation.max_deviation_phase.value} phase"
    )
