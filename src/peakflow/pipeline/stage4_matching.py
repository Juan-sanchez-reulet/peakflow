"""
Stage 4: Reference Matching
Compute pose embeddings and match to pro reference library via KNN.
"""

import json
from pathlib import Path

import numpy as np
from sklearn.neighbors import NearestNeighbors

from peakflow.config import settings
from peakflow.models.schemas import (
    PoseSequence,
    ReferenceClip,
    MatchResult,
    Stance,
    Direction,
    ManeuverType,
)


class ReferenceMatcher:
    """Matches user poses to pro reference library."""

    def __init__(self, reference_dir: Path | None = None):
        self.reference_dir = reference_dir or settings.REFERENCE_DIR
        self.manifest: list[ReferenceClip] = []
        self.embeddings: dict[str, np.ndarray] = {}
        self._load_references()

    def _load_references(self):
        """Load reference manifest and pre-computed embeddings."""
        manifest_path = self.reference_dir / "manifest.json"

        if not manifest_path.exists():
            # No references available yet - create empty manifest
            self.manifest = []
            return

        with open(manifest_path) as f:
            manifest_data = json.load(f)

        # Support both "clips" (new format) and "references" (legacy)
        entries = manifest_data.get("clips", manifest_data.get("references", []))
        for entry in entries:
            clip = ReferenceClip(
                clip_id=entry["clip_id"],
                maneuver=ManeuverType(entry["maneuver"]),
                stance=Stance(entry["stance"]),
                direction=Direction(entry["direction"]),
                style_tags=entry.get("style_tags", []),
                surfer_name=entry.get("surfer_name", "Unknown"),
                source=entry.get("source", ""),
                camera_angle=entry.get("camera_angle", "side"),
                quality_score=entry.get("quality_score", 5),
                pose_file=entry.get("pose_file", ""),
                embedding_file=entry.get("embedding_file", ""),
            )
            self.manifest.append(clip)

            # Load pre-computed embedding if available
            embedding_path = self.reference_dir / clip.embedding_file
            if embedding_path.exists():
                self.embeddings[clip.clip_id] = np.load(embedding_path)

    def compute_embedding(self, pose_sequence: PoseSequence) -> np.ndarray:
        """
        Compute embedding for a pose sequence.

        Uses statistics-based features:
        - Mean joint angles
        - Std of joint angles
        - Range of motion
        - Timing features (peak positions)
        """
        features = []

        # Extract joint angles for all frames
        angles_over_time = []

        for frame in pose_sequence.frames:
            frame_angles = self._compute_frame_angles(frame)
            angles_over_time.append(frame_angles)

        angles_array = np.array(angles_over_time)  # (T, num_angles)

        # Statistical features
        features.extend(np.mean(angles_array, axis=0))  # Mean of each angle
        features.extend(np.std(angles_array, axis=0))  # Std of each angle
        features.extend(np.max(angles_array, axis=0) - np.min(angles_array, axis=0))  # Range

        # Timing features - when does each angle reach its peak?
        peak_positions = np.argmax(angles_array, axis=0) / len(angles_array)
        features.extend(peak_positions)

        return np.array(features)

    def _compute_frame_angles(self, frame) -> list[float]:
        """Compute key joint angles from a single frame."""
        landmarks = frame.landmarks

        # MediaPipe indices
        LEFT_HIP, RIGHT_HIP = 23, 24
        LEFT_KNEE, RIGHT_KNEE = 25, 26
        LEFT_ANKLE, RIGHT_ANKLE = 27, 28
        LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12

        def get_xyz(idx):
            return np.array([landmarks[idx].x, landmarks[idx].y, landmarks[idx].z])

        def angle_3points(a, b, c):
            """Angle at point b formed by points a-b-c."""
            ba = a - b
            bc = c - b
            cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

        # Compute angles
        left_knee_angle = angle_3points(
            get_xyz(LEFT_HIP), get_xyz(LEFT_KNEE), get_xyz(LEFT_ANKLE)
        )
        right_knee_angle = angle_3points(
            get_xyz(RIGHT_HIP), get_xyz(RIGHT_KNEE), get_xyz(RIGHT_ANKLE)
        )
        left_hip_angle = angle_3points(
            get_xyz(LEFT_SHOULDER), get_xyz(LEFT_HIP), get_xyz(LEFT_KNEE)
        )
        right_hip_angle = angle_3points(
            get_xyz(RIGHT_SHOULDER), get_xyz(RIGHT_HIP), get_xyz(RIGHT_KNEE)
        )

        # Compression (hip height relative to stance)
        hip_y = (landmarks[LEFT_HIP].y + landmarks[RIGHT_HIP].y) / 2
        ankle_y = (landmarks[LEFT_ANKLE].y + landmarks[RIGHT_ANKLE].y) / 2
        compression = hip_y - ankle_y

        return [
            left_knee_angle,
            right_knee_angle,
            left_hip_angle,
            right_hip_angle,
            compression * 100,  # Scale for embedding
        ]

    def match(
        self,
        user_embedding: np.ndarray,
        stance: Stance,
        direction: Direction,
        maneuver: ManeuverType = ManeuverType.BOTTOM_TURN,
    ) -> MatchResult:
        """
        Match user embedding to reference library.

        Filters by stance and direction, then uses KNN on embeddings.
        """
        # Filter references by stance, direction, and maneuver type
        filtered_refs = [
            ref
            for ref in self.manifest
            if (ref.stance == stance or ref.stance == Stance.UNKNOWN)
            and (ref.direction == direction or ref.direction == Direction.UNKNOWN)
            and ref.maneuver == maneuver
        ]

        if not filtered_refs:
            # No matching references - return empty result
            return MatchResult(
                matched_references=[],
                style_cluster="unknown",
                similarity_scores=[],
            )

        # Get embeddings for filtered references
        filtered_embeddings = []
        filtered_clip_ids = []

        for ref in filtered_refs:
            if ref.clip_id in self.embeddings:
                filtered_embeddings.append(self.embeddings[ref.clip_id])
                filtered_clip_ids.append(ref.clip_id)

        if not filtered_embeddings:
            # No embeddings available
            return MatchResult(
                matched_references=filtered_refs[: settings.TOP_K_REFERENCES],
                style_cluster="default",
                similarity_scores=[0.5] * min(len(filtered_refs), settings.TOP_K_REFERENCES),
            )

        # Build temporary KNN for filtered set
        embedding_matrix = np.vstack(filtered_embeddings)
        n_neighbors = min(settings.TOP_K_REFERENCES, len(filtered_clip_ids))

        knn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
        knn.fit(embedding_matrix)

        # Find nearest neighbors
        distances, indices = knn.kneighbors(user_embedding.reshape(1, -1))

        # Convert to similarity scores (1 - cosine distance)
        similarity_scores = (1 - distances[0]).tolist()

        # Get matched references
        matched_refs = []
        for idx in indices[0]:
            clip_id = filtered_clip_ids[idx]
            ref = next(r for r in filtered_refs if r.clip_id == clip_id)
            matched_refs.append(ref)

        # Determine style cluster based on tags
        style_cluster = self._determine_style_cluster(matched_refs)

        return MatchResult(
            matched_references=matched_refs,
            style_cluster=style_cluster,
            similarity_scores=similarity_scores,
        )

    def _determine_style_cluster(self, refs: list[ReferenceClip]) -> str:
        """Determine dominant style cluster from matched references."""
        if not refs:
            return "unknown"

        # Count style tags
        tag_counts: dict[str, int] = {}
        for ref in refs:
            for tag in ref.style_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if not tag_counts:
            return "balanced"

        # Return most common tag
        return max(tag_counts, key=tag_counts.get)

    def load_reference_poses(self, ref: ReferenceClip) -> PoseSequence | None:
        """Load pose sequence for a reference clip."""
        pose_path = self.reference_dir / ref.pose_file

        if not pose_path.exists():
            return None

        # Load numpy array and convert to PoseSequence
        # Format: (T, 33, 4) where last dim is [x, y, z, visibility]
        poses_array = np.load(pose_path)

        from peakflow.models.schemas import FramePose, PoseLandmark

        frames = []
        for i, frame_data in enumerate(poses_array):
            landmarks = []
            for lm_data in frame_data:
                landmarks.append(
                    PoseLandmark(
                        x=float(lm_data[0]),
                        y=float(lm_data[1]),
                        z=float(lm_data[2]),
                        visibility=float(lm_data[3]) if len(lm_data) > 3 else 1.0,
                    )
                )
            frames.append(
                FramePose(
                    frame_idx=i,
                    landmarks=landmarks,
                    overall_confidence=1.0,  # Pro references assumed high quality
                )
            )

        return PoseSequence(
            frames=frames,
            fps=30.0,  # Default; should be stored in manifest
            total_duration_ms=len(frames) / 30.0 * 1000,
        )
