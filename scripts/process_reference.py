#!/usr/bin/env python3
"""
Reference Clip Processing Script for PeakFlow

Process pro surf clips and add them to the reference library.
Extracts poses, computes embeddings, and updates the manifest.

Usage:
    python scripts/process_reference.py add --video path/to/clip.mp4 --surfer "Gabriel Medina" ...
    python scripts/process_reference.py list
    python scripts/process_reference.py remove --id bt_regular_fs_001
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from peakflow.config import settings
from peakflow.pipeline.stage1_gating import run_gating
from peakflow.pipeline.stage3_pose import PoseExtractor
from peakflow.pipeline.stage4_matching import ReferenceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Maneuver abbreviations for clip IDs
MANEUVER_ABBREV = {
    "bottom_turn": "bt",
    "cutback": "cb",
    "top_turn": "tt",
}

# Default manifest structure
DEFAULT_MANIFEST = {
    "version": "1.0",
    "clips": [],
}


def ensure_directories(reference_dir: Path) -> None:
    """Create reference directories if they don't exist."""
    (reference_dir / "clips").mkdir(parents=True, exist_ok=True)
    (reference_dir / "poses").mkdir(parents=True, exist_ok=True)
    (reference_dir / "embeddings").mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directories exist at {reference_dir}")


def load_manifest(reference_dir: Path) -> dict:
    """Load manifest.json or create default if not exists."""
    manifest_path = reference_dir / "manifest.json"

    if not manifest_path.exists():
        logger.info("Creating new manifest.json")
        save_manifest(reference_dir, DEFAULT_MANIFEST)
        return DEFAULT_MANIFEST.copy()

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Migrate old format if needed (references -> clips)
    if "references" in manifest and "clips" not in manifest:
        manifest["clips"] = manifest.pop("references")
        save_manifest(reference_dir, manifest)
        logger.info("Migrated manifest from 'references' to 'clips' format")

    return manifest


def save_manifest(reference_dir: Path, manifest: dict) -> None:
    """Save manifest.json with proper formatting."""
    manifest_path = reference_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.debug(f"Saved manifest to {manifest_path}")


def generate_clip_id(
    manifest: dict,
    maneuver: str,
    stance: str,
    direction: str,
    style_tags: list[str],
) -> str:
    """
    Generate clip ID in format: {maneuver_abbrev}_{stance}_{direction}_{style}_{counter:03d}
    Example: bt_regular_fs_power_001
    """
    maneuver_abbr = MANEUVER_ABBREV.get(maneuver, maneuver[:2])
    stance_abbr = stance[:3] if stance != "regular" else "regular"
    direction_abbr = "fs" if direction == "frontside" else "bs"
    style_abbr = style_tags[0] if style_tags else "default"

    # Find next available counter
    prefix = f"{maneuver_abbr}_{stance_abbr}_{direction_abbr}_{style_abbr}_"
    existing_ids = [c["clip_id"] for c in manifest.get("clips", [])]

    counter = 1
    while f"{prefix}{counter:03d}" in existing_ids:
        counter += 1

    return f"{prefix}{counter:03d}"


def pose_sequence_to_numpy(pose_sequence) -> np.ndarray:
    """
    Convert PoseSequence to numpy array.
    Output shape: (T, 33, 4) where last dim is [x, y, z, visibility]
    """
    frames_data = []
    for frame in pose_sequence.frames:
        landmarks_data = []
        for lm in frame.landmarks:
            landmarks_data.append([lm.x, lm.y, lm.z, lm.visibility])
        frames_data.append(landmarks_data)

    return np.array(frames_data, dtype=np.float32)


def add_reference(args, reference_dir: Path) -> int:
    """Add a new reference clip to the library."""
    video_path = Path(args.video)

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return 1

    logger.info(f"Processing video: {video_path}")

    # Ensure directories exist
    ensure_directories(reference_dir)

    # Load manifest
    manifest = load_manifest(reference_dir)

    # Parse style tags
    style_tags = [s.strip() for s in args.style.split(",")] if args.style else []

    # Generate clip ID
    clip_id = generate_clip_id(
        manifest,
        args.maneuver,
        args.stance,
        args.direction,
        style_tags,
    )

    # Check if clip_id already exists (shouldn't happen with auto-increment, but check anyway)
    existing_ids = [c["clip_id"] for c in manifest.get("clips", [])]
    if clip_id in existing_ids:
        if not args.force:
            response = input(f"Clip ID '{clip_id}' already exists. Overwrite? [y/N]: ")
            if response.lower() != "y":
                logger.info("Aborted by user")
                return 1
        # Remove existing entry
        manifest["clips"] = [c for c in manifest["clips"] if c["clip_id"] != clip_id]
        logger.info(f"Removing existing clip: {clip_id}")

    # Step 1: Validate video passes quality gating
    logger.info("Step 1/5: Running quality gating...")
    gating_result = run_gating(str(video_path))

    if not gating_result.passed:
        logger.error(f"Video failed quality gating: {gating_result.rejection_message}")
        if gating_result.rejection_reason:
            logger.error(f"Rejection reason: {gating_result.rejection_reason.value}")
        return 1

    logger.info(
        f"  Passed: {gating_result.metadata.duration_seconds:.1f}s, "
        f"{gating_result.metadata.width}x{gating_result.metadata.height}, "
        f"{gating_result.metadata.fps:.1f}fps"
    )

    # Step 2: Copy video to clips directory
    logger.info("Step 2/5: Copying video to reference library...")
    video_ext = video_path.suffix.lower()
    dest_video_path = reference_dir / "clips" / f"{clip_id}{video_ext}"
    shutil.copy2(video_path, dest_video_path)
    logger.info(f"  Copied to: {dest_video_path}")

    # Step 3: Extract poses
    logger.info("Step 3/5: Extracting poses (this may take a moment)...")
    try:
        extractor = PoseExtractor()
        pose_sequence, rejection_reason = extractor.process_video(str(video_path))

        if pose_sequence is None:
            logger.error(f"Pose extraction failed: {rejection_reason.value if rejection_reason else 'Unknown error'}")
            # Clean up copied video
            dest_video_path.unlink(missing_ok=True)
            return 1

        logger.info(f"  Extracted {len(pose_sequence.frames)} frames of pose data")

    except Exception as e:
        logger.error(f"Pose extraction error: {e}")
        # Clean up copied video
        dest_video_path.unlink(missing_ok=True)
        return 1

    # Step 4: Save poses as numpy array
    logger.info("Step 4/5: Saving pose data...")
    pose_array = pose_sequence_to_numpy(pose_sequence)
    pose_file = f"{clip_id}.npy"
    pose_path = reference_dir / "poses" / pose_file
    np.save(pose_path, pose_array)
    logger.info(f"  Saved poses: {pose_path} (shape: {pose_array.shape})")

    # Step 5: Compute and save embedding
    logger.info("Step 5/5: Computing embedding...")
    try:
        matcher = ReferenceMatcher(reference_dir)
        embedding = matcher.compute_embedding(pose_sequence)
        embedding_file = f"{clip_id}.npy"
        embedding_path = reference_dir / "embeddings" / embedding_file
        np.save(embedding_path, embedding)
        logger.info(f"  Saved embedding: {embedding_path} (shape: {embedding.shape})")
    except Exception as e:
        logger.error(f"Embedding computation error: {e}")
        # Clean up
        dest_video_path.unlink(missing_ok=True)
        pose_path.unlink(missing_ok=True)
        return 1

    # Step 6: Update manifest
    logger.info("Updating manifest...")
    clip_entry = {
        "clip_id": clip_id,
        "maneuver": args.maneuver,
        "stance": args.stance,
        "direction": args.direction,
        "style_tags": style_tags,
        "surfer_name": args.surfer,
        "source": args.source or "",
        "camera_angle": "lateral_beach",  # Default for now
        "quality_score": args.quality,
        "pose_file": f"poses/{pose_file}",
        "embedding_file": f"embeddings/{embedding_file}",
        "video_file": f"clips/{clip_id}{video_ext}",
        "frame_count": len(pose_sequence.frames),
        "fps": pose_sequence.fps,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest["clips"].append(clip_entry)
    save_manifest(reference_dir, manifest)

    logger.info("=" * 60)
    logger.info(f"Successfully added reference clip: {clip_id}")
    logger.info(f"  Surfer: {args.surfer}")
    logger.info(f"  Maneuver: {args.maneuver}")
    logger.info(f"  Stance: {args.stance}, Direction: {args.direction}")
    logger.info(f"  Style: {', '.join(style_tags) if style_tags else 'none'}")
    logger.info(f"  Frames: {len(pose_sequence.frames)}, FPS: {pose_sequence.fps:.1f}")
    logger.info("=" * 60)

    return 0


def list_references(reference_dir: Path) -> int:
    """List all reference clips in the library."""
    manifest = load_manifest(reference_dir)
    clips = manifest.get("clips", [])

    if not clips:
        logger.info("No reference clips in library.")
        return 0

    print(f"\nReference Library ({len(clips)} clips)")
    print("=" * 80)

    for clip in clips:
        style_str = ", ".join(clip.get("style_tags", [])) or "none"
        print(
            f"\n{clip['clip_id']}"
            f"\n  Surfer:   {clip.get('surfer_name', 'Unknown')}"
            f"\n  Maneuver: {clip['maneuver']}"
            f"\n  Stance:   {clip['stance']}, Direction: {clip['direction']}"
            f"\n  Style:    {style_str}"
            f"\n  Quality:  {clip.get('quality_score', 'N/A')}/5"
            f"\n  Frames:   {clip.get('frame_count', 'N/A')}"
            f"\n  Source:   {clip.get('source', 'N/A')}"
            f"\n  Added:    {clip.get('added_at', 'N/A')}"
        )

    print("\n" + "=" * 80)
    return 0


def remove_reference(args, reference_dir: Path) -> int:
    """Remove a reference clip from the library."""
    clip_id = args.id

    manifest = load_manifest(reference_dir)
    clips = manifest.get("clips", [])

    # Find the clip
    clip_entry = next((c for c in clips if c["clip_id"] == clip_id), None)

    if not clip_entry:
        logger.error(f"Clip not found: {clip_id}")
        return 1

    # Confirm removal
    if not args.force:
        print(f"\nAbout to remove: {clip_id}")
        print(f"  Surfer: {clip_entry.get('surfer_name', 'Unknown')}")
        print(f"  Maneuver: {clip_entry['maneuver']}")
        response = input("\nAre you sure? [y/N]: ")
        if response.lower() != "y":
            logger.info("Aborted by user")
            return 1

    # Remove files
    files_to_remove = [
        reference_dir / clip_entry.get("video_file", ""),
        reference_dir / clip_entry.get("pose_file", ""),
        reference_dir / clip_entry.get("embedding_file", ""),
    ]

    for file_path in files_to_remove:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Removed: {file_path}")

    # Update manifest
    manifest["clips"] = [c for c in clips if c["clip_id"] != clip_id]
    save_manifest(reference_dir, manifest)

    logger.info(f"Successfully removed clip: {clip_id}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PeakFlow Reference Clip Processing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a new reference clip
  python scripts/process_reference.py add \\
    --video path/to/clip.mp4 \\
    --surfer "Gabriel Medina" \\
    --maneuver bottom_turn \\
    --stance regular \\
    --direction frontside \\
    --style power,vertical \\
    --source "WSL Highlights 2023" \\
    --quality 5

  # List all references
  python scripts/process_reference.py list

  # Remove a reference
  python scripts/process_reference.py remove --id bt_regular_fs_power_001
        """,
    )

    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=settings.REFERENCE_DIR,
        help="Path to reference directory (default: data/references)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new reference clip")
    add_parser.add_argument(
        "--video",
        required=True,
        help="Path to the video file",
    )
    add_parser.add_argument(
        "--surfer",
        required=True,
        help="Name of the surfer (e.g., 'Gabriel Medina')",
    )
    add_parser.add_argument(
        "--maneuver",
        required=True,
        choices=["bottom_turn", "cutback", "top_turn"],
        help="Type of maneuver",
    )
    add_parser.add_argument(
        "--stance",
        required=True,
        choices=["regular", "goofy"],
        help="Surfer's stance",
    )
    add_parser.add_argument(
        "--direction",
        required=True,
        choices=["frontside", "backside"],
        help="Direction of the turn",
    )
    add_parser.add_argument(
        "--style",
        default="",
        help="Comma-separated style tags (e.g., 'power,vertical')",
    )
    add_parser.add_argument(
        "--source",
        default="",
        help="Source of the clip (e.g., 'WSL Highlights 2023')",
    )
    add_parser.add_argument(
        "--quality",
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help="Quality score 1-5 (default: 5)",
    )
    add_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force overwrite if clip ID exists",
    )

    # List command
    subparsers.add_parser("list", help="List all reference clips")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a reference clip")
    remove_parser.add_argument(
        "--id",
        required=True,
        help="Clip ID to remove",
    )
    remove_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate command
    if not args.command:
        parser.print_help()
        return 1

    reference_dir = args.reference_dir

    # Execute command
    if args.command == "add":
        return add_reference(args, reference_dir)
    elif args.command == "list":
        return list_references(reference_dir)
    elif args.command == "remove":
        return remove_reference(args, reference_dir)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())