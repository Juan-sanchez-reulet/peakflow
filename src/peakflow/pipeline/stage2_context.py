"""
Stage 2: Context Detection
Detect surfer stance (regular/goofy) and turn direction (frontside/backside).
"""

import numpy as np

from peakflow.models.schemas import (
    ContextResult,
    PoseSequence,
    Stance,
    Direction,
)


# MediaPipe landmark indices
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_KNEE = 25
RIGHT_KNEE = 26


class ContextDetector:
    """Detects stance and direction from pose sequence."""

    def detect(self, pose_sequence: PoseSequence) -> ContextResult:
        """
        Analyze pose sequence to determine stance and direction.

        Stance detection:
        - Regular: Left foot forward (toward direction of travel)
        - Goofy: Right foot forward

        Direction detection:
        - Frontside: Chest facing the wave
        - Backside: Back facing the wave
        """
        # Sample frames from the sequence (use middle portion for stability)
        n_frames = len(pose_sequence.frames)
        start_idx = n_frames // 4
        end_idx = 3 * n_frames // 4
        sample_frames = pose_sequence.frames[start_idx:end_idx]

        if not sample_frames:
            sample_frames = pose_sequence.frames

        # Detect stance
        stance, stance_confidence = self._detect_stance(sample_frames)

        # Detect direction
        direction, direction_confidence = self._detect_direction(sample_frames, stance)

        # Detect wave direction (which way the surfer is traveling)
        wave_direction = self._detect_wave_direction(sample_frames)

        # Combined confidence
        combined_confidence = (stance_confidence + direction_confidence) / 2

        return ContextResult(
            stance=stance,
            direction=direction,
            wave_direction=wave_direction,
            confidence=combined_confidence,
        )

    def _detect_stance(
        self, frames: list
    ) -> tuple[Stance, float]:
        """
        Detect if surfer is regular or goofy based on which foot leads.

        Uses the relative x-position of ankles over time. The foot that's
        consistently more in the direction of travel is the front foot.
        """
        left_leads_count = 0
        right_leads_count = 0
        total_samples = 0

        for frame in frames:
            landmarks = frame.landmarks

            # Get ankle positions
            left_ankle_x = landmarks[LEFT_ANKLE].x
            right_ankle_x = landmarks[RIGHT_ANKLE].x

            # Get hip positions for reference
            left_hip_x = landmarks[LEFT_HIP].x
            right_hip_x = landmarks[RIGHT_HIP].x
            hip_center_x = (left_hip_x + right_hip_x) / 2

            if left_ankle_x < right_ankle_x:
                left_leads_count += 1
            else:
                right_leads_count += 1

            total_samples += 1

        if total_samples == 0:
            return Stance.UNKNOWN, 0.0

        # Determine stance based on majority
        if left_leads_count > right_leads_count:
            stance = Stance.REGULAR  # Left foot forward
            confidence = left_leads_count / total_samples
        elif right_leads_count > left_leads_count:
            stance = Stance.GOOFY  # Right foot forward
            confidence = right_leads_count / total_samples
        else:
            stance = Stance.UNKNOWN
            confidence = 0.5

        return stance, confidence

    def _detect_direction(
        self, frames: list, stance: Stance
    ) -> tuple[Direction, float]:
        """
        Detect if turn is frontside or backside.

        Frontside: Surfer's chest/face is toward the wave
        Backside: Surfer's back is toward the wave

        This is determined by the shoulder orientation relative to
        the direction of travel.
        """
        frontside_count = 0
        backside_count = 0
        total_samples = 0

        for frame in frames:
            landmarks = frame.landmarks

            # Get shoulder positions
            left_shoulder = np.array([
                landmarks[LEFT_SHOULDER].x,
                landmarks[LEFT_SHOULDER].y,
            ])
            right_shoulder = np.array([
                landmarks[RIGHT_SHOULDER].x,
                landmarks[RIGHT_SHOULDER].y,
            ])

            # Get hip positions
            left_hip = np.array([
                landmarks[LEFT_HIP].x,
                landmarks[LEFT_HIP].y,
            ])
            right_hip = np.array([
                landmarks[RIGHT_HIP].x,
                landmarks[RIGHT_HIP].y,
            ])

            # Shoulder vector (left to right)
            shoulder_vec = right_shoulder - left_shoulder

            # Hip vector
            hip_vec = right_hip - left_hip

            # Cross product z-component indicates orientation
            # Positive = facing one way, negative = facing other way
            cross_z = shoulder_vec[0] * hip_vec[1] - shoulder_vec[1] * hip_vec[0]

            # The interpretation depends on stance
            if stance == Stance.REGULAR:
                # Regular: left foot forward
                # Frontside = chest toward wave (typically right side of frame in left-to-right wave)
                if cross_z > 0:
                    frontside_count += 1
                else:
                    backside_count += 1
            elif stance == Stance.GOOFY:
                # Goofy: right foot forward
                # Frontside interpretation is flipped
                if cross_z < 0:
                    frontside_count += 1
                else:
                    backside_count += 1

            total_samples += 1

        if total_samples == 0:
            return Direction.UNKNOWN, 0.0

        # Determine direction based on majority
        if frontside_count > backside_count:
            direction = Direction.FRONTSIDE
            confidence = frontside_count / total_samples
        elif backside_count > frontside_count:
            direction = Direction.BACKSIDE
            confidence = backside_count / total_samples
        else:
            direction = Direction.UNKNOWN
            confidence = 0.5

        return direction, confidence

    def _detect_wave_direction(self, frames: list) -> str:
        """
        Detect which direction the wave/surfer is traveling.

        Returns "left_to_right" or "right_to_left" based on the
        overall movement of the surfer's hip center.
        """
        if len(frames) < 2:
            return "left_to_right"  # Default

        # Get hip center positions at start and end
        first_frame = frames[0]
        last_frame = frames[-1]

        first_hip_x = (
            first_frame.landmarks[LEFT_HIP].x + first_frame.landmarks[RIGHT_HIP].x
        ) / 2
        last_hip_x = (
            last_frame.landmarks[LEFT_HIP].x + last_frame.landmarks[RIGHT_HIP].x
        ) / 2

        # Determine direction based on movement
        if last_hip_x > first_hip_x:
            return "left_to_right"
        else:
            return "right_to_left"
