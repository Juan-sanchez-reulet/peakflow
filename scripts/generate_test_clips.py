#!/usr/bin/env python3
"""
Generate synthetic test clips for PeakFlow testing.

Creates test videos that simulate various amateur surf scenarios
using OpenCV to generate simple animated scenes.

Usage:
    python scripts/generate_test_clips.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from peakflow.config import settings

TEST_CLIPS_DIR = settings.DATA_DIR / "test_clips"


def create_video(
    path: Path,
    width: int,
    height: int,
    fps: float,
    duration_sec: float,
    draw_func=None,
    description: str = "",
):
    """Create a test video with given parameters."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    total_frames = int(fps * duration_sec)
    for frame_idx in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Ocean-like background gradient
        for y in range(height):
            blue_val = int(100 + 80 * (y / height))
            green_val = int(60 + 40 * (y / height))
            frame[y, :] = [blue_val, green_val, 20]

        if draw_func:
            draw_func(frame, frame_idx, total_frames, width, height)

        writer.write(frame)

    writer.release()
    size_kb = path.stat().st_size / 1024
    print(f"  Created: {path.name} ({width}x{height}, {fps}fps, {duration_sec}s, {size_kb:.0f}KB) — {description}")


def draw_surfer(frame, frame_idx, total_frames, w, h):
    """Draw a simple stick figure surfer moving across the frame."""
    progress = frame_idx / max(1, total_frames - 1)

    # Surfer position (moves left to right)
    cx = int(w * 0.2 + w * 0.6 * progress)
    cy = int(h * 0.55)

    # Body (stick figure)
    # Torso
    cv2.line(frame, (cx, cy - 40), (cx, cy + 20), (255, 220, 180), 3)
    # Head
    cv2.circle(frame, (cx, cy - 50), 10, (255, 220, 180), -1)
    # Arms (slightly animated)
    arm_angle = int(20 * np.sin(progress * 6 * np.pi))
    cv2.line(frame, (cx, cy - 20), (cx - 30, cy - 20 + arm_angle), (255, 220, 180), 2)
    cv2.line(frame, (cx, cy - 20), (cx + 30, cy - 20 - arm_angle), (255, 220, 180), 2)
    # Legs (bent for surfing)
    knee_bend = int(10 * np.sin(progress * 4 * np.pi))
    cv2.line(frame, (cx, cy + 20), (cx - 15, cy + 50 + knee_bend), (255, 220, 180), 2)
    cv2.line(frame, (cx, cy + 20), (cx + 15, cy + 50 - knee_bend), (255, 220, 180), 2)
    # Feet
    cv2.line(frame, (cx - 15, cy + 50 + knee_bend), (cx - 25, cy + 55 + knee_bend), (255, 220, 180), 2)
    cv2.line(frame, (cx + 15, cy + 50 - knee_bend), (cx + 25, cy + 55 - knee_bend), (255, 220, 180), 2)

    # Surfboard
    board_y = cy + 58
    cv2.ellipse(frame, (cx, board_y), (40, 5), 0, 0, 360, (200, 180, 120), -1)

    # Wave
    for x in range(0, w, 2):
        wave_y = int(h * 0.7 + 15 * np.sin((x + frame_idx * 3) * 0.02))
        cv2.line(frame, (x, wave_y), (x, h), (180, 140, 60), 1)


def draw_two_people(frame, frame_idx, total_frames, w, h):
    """Draw two stick figures (to test multi-person rejection)."""
    draw_surfer(frame, frame_idx, total_frames, w, h)
    # Second person
    cx2 = int(w * 0.7)
    cy2 = int(h * 0.4)
    cv2.line(frame, (cx2, cy2 - 30), (cx2, cy2 + 15), (255, 200, 150), 3)
    cv2.circle(frame, (cx2, cy2 - 38), 8, (255, 200, 150), -1)
    cv2.line(frame, (cx2, cy2 - 10), (cx2 - 20, cy2), (255, 200, 150), 2)
    cv2.line(frame, (cx2, cy2 - 10), (cx2 + 20, cy2), (255, 200, 150), 2)


def draw_bottom_turn_amateur(frame, frame_idx, total_frames, w, h):
    """Draw an amateur bottom turn — less compression, arms high."""
    progress = frame_idx / max(1, total_frames - 1)
    cx = int(w * 0.3 + w * 0.4 * progress)
    cy = int(h * 0.5)

    # More upright stance (amateur - not enough compression)
    cv2.line(frame, (cx, cy - 50), (cx, cy + 10), (255, 220, 180), 3)
    cv2.circle(frame, (cx, cy - 60), 10, (255, 220, 180), -1)

    # Arms too high (common amateur mistake)
    cv2.line(frame, (cx, cy - 30), (cx - 35, cy - 60), (255, 220, 180), 2)
    cv2.line(frame, (cx, cy - 30), (cx + 35, cy - 55), (255, 220, 180), 2)

    # Legs mostly straight (not compressed enough)
    cv2.line(frame, (cx, cy + 10), (cx - 12, cy + 50), (255, 220, 180), 2)
    cv2.line(frame, (cx, cy + 10), (cx + 12, cy + 50), (255, 220, 180), 2)
    cv2.line(frame, (cx - 12, cy + 50), (cx - 22, cy + 55), (255, 220, 180), 2)
    cv2.line(frame, (cx + 12, cy + 50), (cx + 22, cy + 55), (255, 220, 180), 2)

    # Surfboard
    cv2.ellipse(frame, (cx, cy + 58), (40, 5), -10 * progress, 0, 360, (200, 180, 120), -1)

    # Wave
    for x in range(0, w, 2):
        wave_y = int(h * 0.75 + 12 * np.sin((x + frame_idx * 4) * 0.025))
        cv2.line(frame, (x, wave_y), (x, h), (180, 140, 60), 1)


def draw_cutback_amateur(frame, frame_idx, total_frames, w, h):
    """Draw an amateur cutback attempt."""
    progress = frame_idx / max(1, total_frames - 1)

    # Cutback: surfer goes right then turns back left
    if progress < 0.5:
        cx = int(w * 0.3 + w * 0.3 * (progress * 2))
    else:
        cx = int(w * 0.6 - w * 0.2 * ((progress - 0.5) * 2))

    cy = int(h * 0.5)
    rotation = -30 * np.sin(progress * np.pi)

    cv2.line(frame, (cx, cy - 45), (cx + int(rotation * 0.3), cy + 15), (255, 220, 180), 3)
    cv2.circle(frame, (cx, cy - 55), 10, (255, 220, 180), -1)
    cv2.line(frame, (cx, cy - 20), (cx - 30 + int(rotation * 0.5), cy - 30), (255, 220, 180), 2)
    cv2.line(frame, (cx, cy - 20), (cx + 30 + int(rotation * 0.5), cy - 25), (255, 220, 180), 2)
    cv2.line(frame, (cx + int(rotation * 0.3), cy + 15), (cx - 10, cy + 50), (255, 220, 180), 2)
    cv2.line(frame, (cx + int(rotation * 0.3), cy + 15), (cx + 10, cy + 50), (255, 220, 180), 2)

    cv2.ellipse(frame, (cx, cy + 55), (40, 5), rotation, 0, 360, (200, 180, 120), -1)

    for x in range(0, w, 2):
        wave_y = int(h * 0.72 + 10 * np.sin((x + frame_idx * 3) * 0.03))
        cv2.line(frame, (x, wave_y), (x, h), (180, 140, 60), 1)


def main():
    print(f"\nGenerating test clips in: {TEST_CLIPS_DIR}\n")

    # 1. Valid amateur clips (various maneuvers)
    create_video(
        TEST_CLIPS_DIR / "amateur_bottom_turn_good.mp4",
        width=640, height=480, fps=30, duration_sec=5.0,
        draw_func=draw_bottom_turn_amateur,
        description="Valid amateur bottom turn, 640x480@30fps, 5s",
    )

    create_video(
        TEST_CLIPS_DIR / "amateur_bottom_turn_hd.mp4",
        width=1280, height=720, fps=30, duration_sec=6.0,
        draw_func=draw_bottom_turn_amateur,
        description="Valid HD amateur bottom turn, 720p@30fps, 6s",
    )

    create_video(
        TEST_CLIPS_DIR / "amateur_cutback_good.mp4",
        width=640, height=480, fps=30, duration_sec=7.0,
        draw_func=draw_cutback_amateur,
        description="Valid amateur cutback, 640x480@30fps, 7s",
    )

    create_video(
        TEST_CLIPS_DIR / "amateur_general_surf.mp4",
        width=854, height=480, fps=30, duration_sec=8.0,
        draw_func=draw_surfer,
        description="General surfing clip, 854x480@30fps, 8s",
    )

    # 2. Edge cases — should be rejected
    create_video(
        TEST_CLIPS_DIR / "reject_too_short.mp4",
        width=640, height=480, fps=30, duration_sec=1.5,
        draw_func=draw_surfer,
        description="TOO SHORT — 1.5s (min 3s)",
    )

    create_video(
        TEST_CLIPS_DIR / "reject_too_long.mp4",
        width=640, height=480, fps=30, duration_sec=18.0,
        draw_func=draw_surfer,
        description="TOO LONG — 18s (max 15s)",
    )

    create_video(
        TEST_CLIPS_DIR / "reject_low_resolution.mp4",
        width=320, height=240, fps=30, duration_sec=5.0,
        draw_func=draw_surfer,
        description="LOW RES — 320x240 (min 480p)",
    )

    create_video(
        TEST_CLIPS_DIR / "reject_low_fps.mp4",
        width=640, height=480, fps=15, duration_sec=5.0,
        draw_func=draw_surfer,
        description="LOW FPS — 15fps (min 24fps)",
    )

    create_video(
        TEST_CLIPS_DIR / "reject_multiple_people.mp4",
        width=640, height=480, fps=30, duration_sec=5.0,
        draw_func=draw_two_people,
        description="MULTIPLE PEOPLE — two figures in frame",
    )

    # 3. Variety of valid durations
    for dur in [3.0, 5.0, 10.0, 14.5]:
        create_video(
            TEST_CLIPS_DIR / f"valid_duration_{dur:.0f}s.mp4",
            width=640, height=480, fps=30, duration_sec=dur,
            draw_func=draw_surfer,
            description=f"Valid duration test — {dur}s",
        )

    # 4. Different resolutions (all valid)
    for w, h, label in [(640, 480, "480p"), (1280, 720, "720p"), (1920, 1080, "1080p")]:
        create_video(
            TEST_CLIPS_DIR / f"valid_res_{label}.mp4",
            width=w, height=h, fps=30, duration_sec=5.0,
            draw_func=draw_surfer,
            description=f"Valid resolution — {label}",
        )

    # Summary
    clips = list(TEST_CLIPS_DIR.glob("*.mp4"))
    total_size_mb = sum(c.stat().st_size for c in clips) / (1024 * 1024)
    print(f"\nGenerated {len(clips)} test clips ({total_size_mb:.1f} MB total)")
    print(f"Location: {TEST_CLIPS_DIR}\n")


if __name__ == "__main__":
    main()
