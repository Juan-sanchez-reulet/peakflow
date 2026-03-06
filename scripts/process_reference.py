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
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from peakflow.config import settings
from peakflow.reference.ingestion import (
    ensure_directories,
    load_manifest,
    process_single_clip,
    save_manifest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def add_reference(args, reference_dir: Path) -> int:
    """Add a new reference clip to the library."""
    video_path = Path(args.video)

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return 1

    # Parse style tags
    style_tags = [s.strip() for s in args.style.split(",")] if args.style else []

    result = process_single_clip(
        video_path=video_path,
        maneuver=args.maneuver,
        surfer_name=args.surfer,
        source=args.source or "",
        quality=args.quality,
        style_tags=style_tags,
        reference_dir=reference_dir,
        stance=args.stance,
        direction=args.direction,
    )

    if result.success:
        logger.info("=" * 60)
        logger.info(f"Successfully added reference clip: {result.clip_id}")
        logger.info(f"  Surfer: {args.surfer}")
        logger.info(f"  Maneuver: {args.maneuver}")
        logger.info(f"  Stance: {result.auto_detected_stance}, Direction: {result.auto_detected_direction}")
        logger.info(f"  Style: {', '.join(style_tags) if style_tags else 'none'}")
        logger.info(f"  Frames: {result.frame_count}, FPS: {result.fps:.1f}")
        logger.info(f"  Pose quality: {result.pose_quality_score:.2f}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error(f"Failed: {result.error_message}")
        return 1


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

  # Add with auto-detection (no --stance/--direction needed)
  python scripts/process_reference.py add \\
    --video path/to/clip.mp4 \\
    --surfer "John John Florence" \\
    --maneuver bottom_turn

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
    add_parser.add_argument("--video", required=True, help="Path to the video file")
    add_parser.add_argument("--surfer", required=True, help="Name of the surfer")
    add_parser.add_argument(
        "--maneuver", required=True,
        choices=["bottom_turn", "cutback", "top_turn"],
        help="Type of maneuver",
    )
    add_parser.add_argument("--stance", choices=["regular", "goofy"], help="Surfer's stance (auto-detected if omitted)")
    add_parser.add_argument("--direction", choices=["frontside", "backside"], help="Turn direction (auto-detected if omitted)")
    add_parser.add_argument("--style", default="", help="Comma-separated style tags")
    add_parser.add_argument("--source", default="", help="Source of the clip")
    add_parser.add_argument("--quality", type=int, default=5, choices=[1, 2, 3, 4, 5], help="Quality score 1-5")
    add_parser.add_argument("-f", "--force", action="store_true", help="Force overwrite")

    # List command
    subparsers.add_parser("list", help="List all reference clips")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a reference clip")
    remove_parser.add_argument("--id", required=True, help="Clip ID to remove")
    remove_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.command:
        parser.print_help()
        return 1

    reference_dir = args.reference_dir

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
