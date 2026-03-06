#!/usr/bin/env python3
"""
Extract and label surf maneuver clips from highlight reels.

Usage:
    python scripts/extract_clips.py interactive --video data/downloads/wsl_pipe_2024.mp4
    python scripts/extract_clips.py from-timestamps --video data/downloads/video.mp4 --timestamps ts.json
    python scripts/extract_clips.py list-staged
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from peakflow.config import settings
from peakflow.pipeline.stage1_gating import run_gating

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

STAGING_DIR = settings.DATA_DIR / "staging"
STAGING_CLIPS_DIR = STAGING_DIR / "clips"
LABELS_FILE = STAGING_DIR / "labels.json"

VALID_MANEUVERS = ["bottom_turn", "cutback", "top_turn"]


def ensure_staging_dirs():
    STAGING_CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def load_labels() -> dict:
    if LABELS_FILE.exists():
        with open(LABELS_FILE) as f:
            return json.load(f)
    return {"version": "1.0", "clips": []}


def save_labels(labels: dict):
    ensure_staging_dirs()
    with open(LABELS_FILE, "w") as f:
        json.dump(labels, f, indent=2)


def parse_time(time_str: str) -> float:
    """Parse flexible time format (ss, mm:ss, hh:mm:ss) to seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid time format: {time_str}")


def format_time(seconds: float) -> str:
    """Format seconds to mm:ss."""
    m = int(seconds) // 60
    s = seconds - m * 60
    return f"{m}:{s:05.2f}"


def get_next_staging_id(labels: dict) -> str:
    """Get next available staging clip ID."""
    existing = [c["staging_id"] for c in labels.get("clips", [])]
    counter = 1
    while f"clip_{counter:03d}" in existing:
        counter += 1
    return f"clip_{counter:03d}"


def trim_clip(video_path: Path, start_sec: float, end_sec: float, output_path: Path) -> bool:
    """Trim a video segment using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-ss", str(start_sec),
        "-to", str(end_sec),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-loglevel", "warning",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, timeout=60, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            return False
        return output_path.exists()
    except subprocess.TimeoutExpired:
        logger.error("Trim timed out")
        return False


def validate_clip(clip_path: Path) -> tuple[bool, str]:
    """Quick validation of trimmed clip."""
    result = run_gating(str(clip_path))
    if result.passed and result.metadata:
        info = f"{result.metadata.width}x{result.metadata.height}, {result.metadata.fps:.0f}fps, {result.metadata.duration_seconds:.1f}s"
        return True, info
    return False, result.rejection_message or "Unknown validation error"


def interactive_extract(args):
    """Interactive clip extraction from a video."""
    video_path = Path(args.video)
    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        return 1

    if not shutil.which("ffmpeg"):
        logger.error("ffmpeg not found. Install with: brew install ffmpeg")
        return 1

    ensure_staging_dirs()
    labels = load_labels()

    # Open video in system player
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(video_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Opened video: {video_path.name}")

    print(f"\n{'='*60}")
    print(f"  PeakFlow Clip Extractor — Interactive Mode")
    print(f"  Video: {video_path.name}")
    print(f"{'='*60}")
    print(f"\n  Watch the video and enter maneuver timestamps below.")
    print(f"  Time format: mm:ss or just seconds (e.g., 1:23 or 83)")
    print(f"  Type 'done' to finish.\n")

    segment_num = 0
    while True:
        segment_num += 1
        print(f"\n--- Segment {segment_num} ---")

        # Start time
        start_input = input("  Start time (or 'done'): ").strip()
        if start_input.lower() == "done":
            break
        try:
            start_sec = parse_time(start_input)
        except ValueError:
            print("  Invalid time. Try again.")
            segment_num -= 1
            continue

        # End time
        end_input = input("  End time: ").strip()
        try:
            end_sec = parse_time(end_input)
        except ValueError:
            print("  Invalid time. Try again.")
            segment_num -= 1
            continue

        duration = end_sec - start_sec
        if duration < 1 or duration > 20:
            print(f"  Duration {duration:.1f}s seems wrong. Skipping.")
            segment_num -= 1
            continue

        # Maneuver type
        print(f"  Maneuver types: {', '.join(VALID_MANEUVERS)}")
        maneuver = input("  Maneuver: ").strip().lower()
        if maneuver not in VALID_MANEUVERS:
            print(f"  Invalid maneuver. Must be one of: {VALID_MANEUVERS}")
            segment_num -= 1
            continue

        # Surfer name
        surfer = input("  Surfer name: ").strip()
        if not surfer:
            print("  Surfer name is required.")
            segment_num -= 1
            continue

        # Style tags
        style_input = input("  Style tags (comma-separated, or empty): ").strip()
        style_tags = [s.strip() for s in style_input.split(",") if s.strip()] if style_input else []

        # Quality
        quality_input = input("  Quality 1-5 (default 5): ").strip()
        quality = int(quality_input) if quality_input and quality_input.isdigit() else 5
        quality = max(1, min(5, quality))

        # Source
        source = input("  Source description (default: filename): ").strip()
        if not source:
            source = video_path.stem

        # Trim
        staging_id = get_next_staging_id(labels)
        output_path = STAGING_CLIPS_DIR / f"{staging_id}.mp4"

        print(f"\n  Trimming {format_time(start_sec)} -> {format_time(end_sec)} ({duration:.1f}s)...")
        if not trim_clip(video_path, start_sec, end_sec, output_path):
            print("  Trim failed! Skipping.")
            segment_num -= 1
            continue

        # Validate
        valid, info = validate_clip(output_path)
        if valid:
            print(f"  Validated: {info} -- PASS")
        else:
            print(f"  Warning: {info}")
            keep = input("  Keep anyway? [Y/n]: ").strip()
            if keep.lower() == "n":
                output_path.unlink(missing_ok=True)
                segment_num -= 1
                continue

        # Save label
        labels["clips"].append({
            "staging_id": staging_id,
            "file": f"clips/{staging_id}.mp4",
            "source_video": video_path.name,
            "start_time": start_input,
            "end_time": end_input,
            "maneuver": maneuver,
            "surfer_name": surfer,
            "style_tags": style_tags,
            "quality_score": quality,
            "source": source,
            "status": "staged",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        save_labels(labels)
        print(f"  Saved: {staging_id} ({maneuver} by {surfer})")

    # Summary
    staged_count = sum(1 for c in labels["clips"] if c["status"] == "staged")
    print(f"\n{'='*60}")
    print(f"  Done! {staged_count} clips staged for processing.")
    print(f"  Run: python scripts/batch_process.py dry-run")
    print(f"{'='*60}\n")
    return 0


def from_timestamps(args):
    """Extract clips from a JSON timestamps file."""
    video_path = Path(args.video)
    ts_path = Path(args.timestamps)

    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        return 1
    if not ts_path.exists():
        logger.error(f"Timestamps file not found: {ts_path}")
        return 1

    with open(ts_path) as f:
        timestamps = json.load(f)

    ensure_staging_dirs()
    labels = load_labels()
    success = 0

    segments = timestamps if isinstance(timestamps, list) else timestamps.get("segments", [])

    for seg in segments:
        start_sec = parse_time(str(seg["start"]))
        end_sec = parse_time(str(seg["end"]))

        staging_id = get_next_staging_id(labels)
        output_path = STAGING_CLIPS_DIR / f"{staging_id}.mp4"

        logger.info(f"Trimming {staging_id}: {format_time(start_sec)} -> {format_time(end_sec)}")
        if not trim_clip(video_path, start_sec, end_sec, output_path):
            logger.error(f"  Failed to trim {staging_id}")
            continue

        valid, info = validate_clip(output_path)
        if not valid:
            logger.warning(f"  Validation warning: {info}")

        labels["clips"].append({
            "staging_id": staging_id,
            "file": f"clips/{staging_id}.mp4",
            "source_video": video_path.name,
            "start_time": str(seg["start"]),
            "end_time": str(seg["end"]),
            "maneuver": seg.get("maneuver", "bottom_turn"),
            "surfer_name": seg.get("surfer", "Unknown"),
            "style_tags": seg.get("style_tags", []),
            "quality_score": seg.get("quality", 5),
            "source": seg.get("source", video_path.stem),
            "status": "staged",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        save_labels(labels)
        success += 1

    logger.info(f"Extracted {success}/{len(segments)} clips")
    return 0


def list_staged(args):
    """List all clips in the staging area."""
    labels = load_labels()
    clips = labels.get("clips", [])

    if not clips:
        print("\nNo staged clips.")
        return 0

    staged = [c for c in clips if c.get("status") == "staged"]
    processed = [c for c in clips if c.get("status") == "processed"]
    failed = [c for c in clips if c.get("status") == "failed"]

    print(f"\nStaging Area ({len(clips)} total: {len(staged)} staged, {len(processed)} processed, {len(failed)} failed)")
    print("=" * 80)

    for clip in clips:
        status_icon = {"staged": "[ ]", "processed": "[+]", "failed": "[!]"}.get(clip["status"], "[?]")
        print(
            f"\n  {status_icon} {clip['staging_id']}"
            f"\n      Maneuver: {clip['maneuver']} | Surfer: {clip['surfer_name']}"
            f"\n      Source:   {clip['source_video']} ({clip['start_time']} -> {clip['end_time']})"
            f"\n      Style:    {', '.join(clip.get('style_tags', [])) or 'none'}"
        )

    print("\n" + "=" * 80)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PeakFlow Clip Extraction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # Interactive
    int_p = subparsers.add_parser("interactive", help="Interactive clip extraction")
    int_p.add_argument("--video", required=True, help="Path to highlight reel video")

    # From timestamps
    ts_p = subparsers.add_parser("from-timestamps", help="Extract from JSON timestamps")
    ts_p.add_argument("--video", required=True, help="Path to highlight reel video")
    ts_p.add_argument("--timestamps", required=True, help="Path to timestamps JSON")

    # List
    subparsers.add_parser("list-staged", help="List staged clips")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "interactive": interactive_extract,
        "from-timestamps": from_timestamps,
        "list-staged": list_staged,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
