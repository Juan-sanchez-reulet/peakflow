"""
Stage 3: Pose Extraction
YOLO detection → SORT tracking → Crop → MediaPipe → Smooth/Filter
"""

import cv2
import numpy as np
import mediapipe as mp
from scipy.signal import savgol_filter
from ultralytics import YOLO

from peakflow.config import settings
from peakflow.models.schemas import (
    PoseSequence,
    FramePose,
    PoseLandmark,
    BoundingBox,
    RejectionReason,
)


class SORTTracker:
    """Simple SORT-style tracker for maintaining identity across frames."""

    def __init__(self, max_age: int = 30):
        self.max_age = max_age
        self.tracks: dict = {}
        self.next_id = 0

    def update(
        self, detections: list[BoundingBox]
    ) -> list[tuple[int, BoundingBox]]:
        """Update tracks with new detections. Returns (track_id, bbox) pairs."""
        # Simplified: for MVP, just track the largest detection
        if not detections:
            return []

        # Find largest detection (most likely the surfer)
        largest = max(detections, key=lambda d: (d.x2 - d.x1) * (d.y2 - d.y1))

        if 0 not in self.tracks:
            self.tracks[0] = {"bbox": largest, "age": 0}
        else:
            self.tracks[0]["bbox"] = largest
            self.tracks[0]["age"] = 0

        return [(0, largest)]

    def reset(self):
        """Reset tracker state."""
        self.tracks = {}
        self.next_id = 0


class PoseExtractor:
    """Handles the full pose extraction pipeline."""

    def __init__(self):
        self.yolo = YOLO(settings.YOLO_MODEL)
        self.tracker = SORTTracker(max_age=settings.TRACKING_MAX_AGE)
        self.mp_pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect_persons(self, frame: np.ndarray, frame_idx: int = 0) -> list[BoundingBox]:
        """Run YOLO to detect persons in frame."""
        results = self.yolo(
            frame, classes=[0], conf=settings.YOLO_CONFIDENCE, verbose=False
        )

        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                detections.append(
                    BoundingBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=conf,
                        frame_idx=frame_idx,
                    )
                )

        return detections

    def crop_with_padding(
        self, frame: np.ndarray, bbox: BoundingBox, padding_ratio: float = 0.2
    ) -> tuple[np.ndarray, tuple[int, int, int, int]]:
        """Crop frame around bbox with padding."""
        h, w = frame.shape[:2]

        # Calculate padding
        box_w = bbox.x2 - bbox.x1
        box_h = bbox.y2 - bbox.y1
        pad_x = int(box_w * padding_ratio)
        pad_y = int(box_h * padding_ratio)

        # Apply padding with bounds checking
        x1 = max(0, int(bbox.x1) - pad_x)
        y1 = max(0, int(bbox.y1) - pad_y)
        x2 = min(w, int(bbox.x2) + pad_x)
        y2 = min(h, int(bbox.y2) + pad_y)

        cropped = frame[y1:y2, x1:x2]
        return cropped, (x1, y1, x2, y2)

    def extract_pose(self, frame: np.ndarray, frame_idx: int = 0) -> FramePose | None:
        """Extract MediaPipe pose from frame."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.mp_pose.process(rgb)

        if not results.pose_landmarks:
            return None

        landmarks = []
        total_visibility = 0

        for lm in results.pose_landmarks.landmark:
            landmarks.append(
                PoseLandmark(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility)
            )
            total_visibility += lm.visibility

        avg_confidence = total_visibility / len(landmarks)

        return FramePose(
            frame_idx=frame_idx,
            landmarks=landmarks,
            overall_confidence=avg_confidence,
        )

    def smooth_sequence(self, poses: list[FramePose]) -> list[FramePose]:
        """Apply Savitzky-Golay smoothing to pose sequence."""
        if len(poses) < settings.POSE_SMOOTHING_WINDOW:
            return poses

        # Extract coordinates into arrays
        n_frames = len(poses)
        n_landmarks = len(poses[0].landmarks)

        coords = np.zeros((n_frames, n_landmarks, 3))
        for i, pose in enumerate(poses):
            for j, lm in enumerate(pose.landmarks):
                coords[i, j] = [lm.x, lm.y, lm.z]

        # Smooth each landmark trajectory
        window = min(settings.POSE_SMOOTHING_WINDOW, n_frames)
        if window % 2 == 0:
            window -= 1
        if window >= 3:
            for j in range(n_landmarks):
                for k in range(3):
                    coords[:, j, k] = savgol_filter(coords[:, j, k], window, 2)

        # Rebuild poses
        smoothed = []
        for i, pose in enumerate(poses):
            new_landmarks = []
            for j, lm in enumerate(pose.landmarks):
                new_landmarks.append(
                    PoseLandmark(
                        x=float(coords[i, j, 0]),
                        y=float(coords[i, j, 1]),
                        z=float(coords[i, j, 2]),
                        visibility=lm.visibility,
                    )
                )
            smoothed.append(
                FramePose(
                    frame_idx=pose.frame_idx,
                    landmarks=new_landmarks,
                    overall_confidence=pose.overall_confidence,
                )
            )

        return smoothed

    def check_camera_angle(self, poses: list[FramePose]) -> RejectionReason | None:
        """
        Check if camera angle is suitable for analysis.

        Rejects head-on or from-behind angles where pose analysis
        would be inaccurate.
        """
        if not poses:
            return RejectionReason.LOW_POSE_CONFIDENCE

        # Sample frames from middle of sequence
        n_frames = len(poses)
        start_idx = n_frames // 4
        end_idx = 3 * n_frames // 4
        sample_frames = poses[start_idx:end_idx]

        if not sample_frames:
            sample_frames = poses

        # MediaPipe indices
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_HIP = 23
        RIGHT_HIP = 24

        ratios = []
        for frame in sample_frames:
            landmarks = frame.landmarks

            # Shoulder width (in image coordinates)
            shoulder_width = abs(
                landmarks[LEFT_SHOULDER].x - landmarks[RIGHT_SHOULDER].x
            )

            # Hip width
            hip_width = abs(landmarks[LEFT_HIP].x - landmarks[RIGHT_HIP].x)

            if hip_width > 0.01:  # Avoid division by zero
                ratio = shoulder_width / hip_width
                ratios.append(ratio)

        if not ratios:
            return None

        avg_ratio = np.mean(ratios)

        # Head-on: shoulders appear much wider than hips
        if avg_ratio > settings.SHOULDER_HIP_RATIO_HEAD_ON:
            return RejectionReason.HEAD_ON_ANGLE

        # From behind: similar issue with proportions
        if avg_ratio < settings.SHOULDER_HIP_RATIO_FROM_BEHIND:
            return RejectionReason.FROM_BEHIND_ANGLE

        return None

    def process_video(
        self, video_path: str
    ) -> tuple[PoseSequence | None, RejectionReason | None]:
        """
        Full pipeline: load video → detect → track → crop → pose → smooth.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Reset tracker for new video
        self.tracker.reset()

        poses = []
        frame_idx = 0
        no_detection_count = 0
        max_no_detection = 10  # Allow some frames without detection

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect persons
            detections = self.detect_persons(frame, frame_idx)

            if not detections:
                no_detection_count += 1
                if no_detection_count > max_no_detection:
                    # Too many frames without detection
                    pass
                frame_idx += 1
                continue

            no_detection_count = 0  # Reset counter

            # Track (get primary track)
            tracks = self.tracker.update(detections)

            if not tracks:
                frame_idx += 1
                continue

            # Crop around tracked person
            _, bbox = tracks[0]
            cropped, _ = self.crop_with_padding(
                frame, bbox, settings.BBOX_PADDING_RATIO
            )

            # Extract pose
            pose = self.extract_pose(cropped, frame_idx)

            if pose:
                if pose.overall_confidence >= settings.POSE_MIN_CONFIDENCE:
                    poses.append(pose)

            frame_idx += 1

        cap.release()

        # Check if we got enough poses
        if len(poses) < 10:
            return None, RejectionReason.LOW_POSE_CONFIDENCE

        # Check camera angle
        angle_rejection = self.check_camera_angle(poses)
        if angle_rejection:
            return None, angle_rejection

        # Smooth sequence
        smoothed = self.smooth_sequence(poses)

        duration_ms = (frame_idx / fps) * 1000 if fps > 0 else 0

        return (
            PoseSequence(frames=smoothed, fps=fps, total_duration_ms=duration_ms),
            None,
        )

    def __del__(self):
        """Cleanup MediaPipe resources."""
        if hasattr(self, "mp_pose"):
            self.mp_pose.close()
