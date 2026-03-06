#!/usr/bin/env python3
"""
Batch process staged clips into the PeakFlow reference library.

Usage:
    python scripts/batch_process.py dry-run
    python scripts/batch_process.py run
    python scripts/batch_process.py run --ids clip_001 clip_003
    python scripts/batch_process.py status
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from peakflow.config import settings
from peakflow.pipeline.stage2_context import ContextDetector
from peakflow.pipeline.stage3_pose import PoseExtractor
from peakflow.reference.ingestion import process_single_clip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

STAGING_DIR = settings.DATA_DIR / "staging"
LABELS_FILE = STAGING_DIR / "labels.json"


def load_labels() -> dict:
    if LABELS_FILE.exists():
        with open(LABELS_FILE) as f:
            return json.load(f)
    return {"version": "1.0", "clips": []}


def save_labels(labels: dict):
    with open(LABELS_FILE, "w") as f:
        json.dump(labels, f, indent=2)


def get_processable_clips(labels: dict, specific_ids: list[str] = None) -> list[dict]:
    """Get clips that are ready to process."""
    clips = labels.get("clips", [])
    if specific_ids:
        return [c for c in clips if c["staging_id"] in specific_ids and c.get("status") == "staged"]
    return [c for c in clips if c.get("status") == "staged"]


def dry_run(args):
    """Preview what would be processed."""
    labels = load_labels()
    clips = labels.get("clips", [])

    staged = [c for c in clips if c.get("status") == "staged"]
    processed = [c for c in clips if c.get("status") == "processed"]
    failed = [c for c in clips if c.get("status") == "failed"]

    print(f"\n{'='*60}")
    print(f"  Batch Processing Dry Run")
    print(f"{'='*60}\n")

    if not clips:
        print("  No clips in staging area.")
        print("  Run: python scripts/extract_clips.py interactive --video <path>")
        return 0

    print(f"  Found {len(clips)} clips in staging:\n")

    for clip in clips:
        status_map = {"staged": "READY", "processed": "ALREADY DONE", "failed": "FAILED"}
        status = status_map.get(clip["status"], clip["status"])
        file_path = STAGING_DIR / clip["file"]
        exists = file_path.exists()

        print(
            f"    {clip['staging_id']:12s} | {clip['maneuver']:12s} | "
            f"{clip['surfer_name']:20s} | {', '.join(clip.get('style_tags', [])) or 'default':10s} | "
            f"{'FILE OK' if exists else 'MISSING':8s} | {status}"
        )

    print(f"\n  Will process: {len(staged)} clips ({len(processed)} already done, {len(failed)} failed)")
    if staged:
        est_time = len(staged) * 35  # ~35 sec per clip
        print(f"  Estimated time: ~{est_time//60}m {est_time%60}s ({35}s per clip)")

    print(f"\n  To process: python scripts/batch_process.py run\n")
    return 0


def run_batch(args):
    """Process staged clips through the reference pipeline."""
    labels = load_labels()
    specific_ids = args.ids if hasattr(args, "ids") and args.ids else None
    processable = get_processable_clips(labels, specific_ids)

    if not processable:
        logger.info("No clips to process.")
        return 0

    reference_dir = Path(args.reference_dir) if hasattr(args, "reference_dir") else settings.REFERENCE_DIR

    logger.info(f"Processing {len(processable)} clips...")
    logger.info("Loading models (first clip will be slower)...\n")

    # Pre-load models for reuse across batch
    pose_extractor = PoseExtractor()
    context_detector = ContextDetector()

    success_count = 0
    fail_count = 0
    results = []
    start_time = time.time()

    for i, clip in enumerate(processable):
        clip_start = time.time()
        staging_id = clip["staging_id"]
        clip_path = STAGING_DIR / clip["file"]

        logger.info(f"[{i+1}/{len(processable)}] Processing {staging_id}: {clip['maneuver']} by {clip['surfer_name']}")

        if not clip_path.exists():
            logger.error(f"  File missing: {clip_path}")
            clip["status"] = "failed"
            clip["error"] = "File not found"
            fail_count += 1
            save_labels(labels)
            continue

        result = process_single_clip(
            video_path=clip_path,
            maneuver=clip["maneuver"],
            surfer_name=clip["surfer_name"],
            source=clip.get("source", ""),
            quality=clip.get("quality_score", 5),
            style_tags=clip.get("style_tags", []),
            reference_dir=reference_dir,
            pose_extractor=pose_extractor,
            context_detector=context_detector,
        )

        elapsed = time.time() - clip_start

        if result.success:
            clip["status"] = "processed"
            clip["clip_id"] = result.clip_id
            clip["detected_stance"] = result.auto_detected_stance
            clip["detected_direction"] = result.auto_detected_direction
            clip["detection_confidence"] = result.detection_confidence
            clip["pose_quality"] = result.pose_quality_score
            success_count += 1
            logger.info(
                f"  OK: {result.clip_id} | stance={result.auto_detected_stance}, "
                f"dir={result.auto_detected_direction} | quality={result.pose_quality_score:.2f} | {elapsed:.1f}s"
            )
        else:
            clip["status"] = "failed"
            clip["error"] = result.error_message
            fail_count += 1
            logger.error(f"  FAILED: {result.error_message} | {elapsed:.1f}s")

        save_labels(labels)
        results.append(result)

    total_time = time.time() - start_time

    # Summary
    print(f"\n{'='*60}")
    print(f"  Batch Processing Complete")
    print(f"{'='*60}")
    print(f"  Processed: {len(processable)} clips in {total_time:.1f}s")
    print(f"  Success:   {success_count}")
    print(f"  Failed:    {fail_count}")
    if success_count > 0:
        print(f"\n  Run: python scripts/coverage_report.py")
    print(f"{'='*60}\n")

    return 0 if fail_count == 0 else 1


def show_status(args):
    """Show processing status of all staged clips."""
    labels = load_labels()
    clips = labels.get("clips", [])

    if not clips:
        print("\nNo clips in staging.")
        return 0

    staged = sum(1 for c in clips if c.get("status") == "staged")
    processed = sum(1 for c in clips if c.get("status") == "processed")
    failed = sum(1 for c in clips if c.get("status") == "failed")

    print(f"\n{'='*60}")
    print(f"  Batch Processing Status")
    print(f"{'='*60}")
    print(f"  Total:     {len(clips)}")
    print(f"  Staged:    {staged} (ready to process)")
    print(f"  Processed: {processed}")
    print(f"  Failed:    {failed}")

    if failed > 0:
        print(f"\n  Failed clips:")
        for c in clips:
            if c.get("status") == "failed":
                print(f"    {c['staging_id']}: {c.get('error', 'Unknown error')}")

    if processed > 0:
        print(f"\n  Processed clips:")
        for c in clips:
            if c.get("status") == "processed":
                print(
                    f"    {c['staging_id']} -> {c.get('clip_id', '?')} "
                    f"({c.get('detected_stance', '?')}/{c.get('detected_direction', '?')}, "
                    f"quality={c.get('pose_quality', '?')})"
                )

    print(f"{'='*60}\n")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PeakFlow Batch Reference Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--reference-dir", type=Path, default=settings.REFERENCE_DIR)

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("dry-run", help="Preview what will be processed")

    run_p = subparsers.add_parser("run", help="Process all staged clips")
    run_p.add_argument("--ids", nargs="*", help="Specific clip IDs to process")

    subparsers.add_parser("status", help="Show processing status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "dry-run": dry_run,
        "run": run_batch,
        "status": show_status,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
