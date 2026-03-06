#!/usr/bin/env python3
"""
Reference library coverage report for PeakFlow.

Displays a matrix showing which maneuver/stance/direction combinations
are covered and which need more clips.

Usage:
    python scripts/coverage_report.py
    python scripts/coverage_report.py --gaps-only
    python scripts/coverage_report.py --json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from peakflow.config import settings

MANEUVERS = ["bottom_turn", "cutback", "top_turn"]
STANCES = ["regular", "goofy"]
DIRECTIONS = ["frontside", "backside"]
KNN_READY_THRESHOLD = 3  # Minimum clips for KNN K=3


def load_manifest(reference_dir: Path) -> dict:
    manifest_path = reference_dir / "manifest.json"
    if not manifest_path.exists():
        return {"version": "1.0", "clips": []}
    with open(manifest_path) as f:
        return json.load(f)


def build_coverage_matrix(clips: list) -> dict:
    """Build a 3D coverage matrix: maneuver -> stance -> direction -> count."""
    matrix = {}
    for m in MANEUVERS:
        matrix[m] = {}
        for s in STANCES:
            matrix[m][s] = {}
            for d in DIRECTIONS:
                matrix[m][s][d] = []

    for clip in clips:
        m = clip.get("maneuver", "")
        s = clip.get("stance", "")
        d = clip.get("direction", "")
        if m in matrix and s in matrix.get(m, {}) and d in matrix.get(m, {}).get(s, {}):
            matrix[m][s][d].append(clip)

    return matrix


def print_coverage_table(matrix: dict):
    """Print a formatted coverage matrix."""
    print("\n  Coverage Matrix (clips per combination):\n")
    # Header
    print(f"  {'':16s} | {'frontside':^15s} | {'backside':^15s} |")
    print(f"  {'':16s} | {'regular':>7s} {'goofy':>7s} | {'regular':>7s} {'goofy':>7s} |")
    print(f"  {'-'*16}-|-{'-'*15}-|-{'-'*15}-|")

    for m in MANEUVERS:
        counts = []
        for d in DIRECTIONS:
            for s in STANCES:
                count = len(matrix[m][s][d])
                counts.append(count)

        # Color indicators
        cells = []
        for c in counts:
            if c == 0:
                cells.append(f"{'[  0 ]':>7s}")
            elif c < KNN_READY_THRESHOLD:
                cells.append(f"{'[' + str(c) + '  ]':>7s}")
            else:
                cells.append(f"{'[' + str(c) + ' +]':>7s}")

        print(f"  {m:16s} | {cells[0]} {cells[1]} | {cells[2]} {cells[3]} |")

    print(f"  {'-'*16}-|-{'-'*15}-|-{'-'*15}-|")
    print(f"\n  Legend: [  0 ] = MISSING  [N  ] = needs more  [N +] = KNN-ready (3+)")


def print_summary(matrix: dict, clips: list):
    """Print coverage summary with gaps and stats."""
    total_combos = len(MANEUVERS) * len(STANCES) * len(DIRECTIONS)
    target_clips = total_combos * KNN_READY_THRESHOLD

    covered = 0
    knn_ready = 0
    needs_more = []
    missing = []

    for m in MANEUVERS:
        for s in STANCES:
            for d in DIRECTIONS:
                count = len(matrix[m][s][d])
                combo_name = f"{m} / {s} / {d}"
                if count >= KNN_READY_THRESHOLD:
                    knn_ready += 1
                    covered += 1
                elif count > 0:
                    covered += 1
                    needs_more.append((combo_name, count, KNN_READY_THRESHOLD - count))
                else:
                    missing.append(combo_name)

    print(f"\n  Summary:")
    print(f"    Total clips:    {len(clips)}/{target_clips} target ({100*len(clips)/max(1,target_clips):.1f}%)")
    print(f"    Covered combos: {covered}/{total_combos} ({100*covered/total_combos:.1f}%)")
    print(f"    KNN-ready:      {knn_ready}/{total_combos} ({100*knn_ready/total_combos:.1f}%)")

    if knn_ready > 0:
        print(f"\n  KNN-READY (3+ clips):")
        for m in MANEUVERS:
            for s in STANCES:
                for d in DIRECTIONS:
                    count = len(matrix[m][s][d])
                    if count >= KNN_READY_THRESHOLD:
                        print(f"    + {m} / {s} / {d} ({count} clips)")

    if needs_more:
        print(f"\n  NEEDS MORE (1-2 clips):")
        for combo, count, need in needs_more:
            print(f"    ~ {combo} ({count} clips, need {need}+ more)")

    if missing:
        print(f"\n  MISSING (0 clips, PRIORITY):")
        for combo in missing:
            print(f"    ! {combo} -- NO CLIPS")

    # Surfer distribution
    surfers = Counter(c.get("surfer_name", "Unknown") for c in clips)
    if surfers:
        print(f"\n  Surfer Distribution:")
        for surfer, count in surfers.most_common():
            stances = set(c.get("stance", "?") for c in clips if c.get("surfer_name") == surfer)
            print(f"    {surfer}: {count} clips ({', '.join(stances)})")

    # Style distribution
    styles = Counter()
    for c in clips:
        for tag in c.get("style_tags", []):
            styles[tag] += 1
    if styles:
        print(f"\n  Style Distribution:")
        for style, count in styles.most_common():
            print(f"    {style}: {count} clips")


def print_gaps_only(matrix: dict):
    """Print only missing and underrepresented combinations."""
    print("\n  Gaps in Reference Library:\n")
    found_gaps = False

    for m in MANEUVERS:
        for s in STANCES:
            for d in DIRECTIONS:
                count = len(matrix[m][s][d])
                if count < KNN_READY_THRESHOLD:
                    found_gaps = True
                    need = KNN_READY_THRESHOLD - count
                    status = "MISSING" if count == 0 else f"have {count}, need {need} more"
                    print(f"  {m:12s} / {s:8s} / {d:10s} -- {status}")

    if not found_gaps:
        print("  All combinations have 3+ clips. Library is fully covered!")


def output_json(matrix: dict, clips: list):
    """Output coverage data as JSON."""
    data = {
        "total_clips": len(clips),
        "target_clips": len(MANEUVERS) * len(STANCES) * len(DIRECTIONS) * KNN_READY_THRESHOLD,
        "matrix": {},
    }
    for m in MANEUVERS:
        data["matrix"][m] = {}
        for s in STANCES:
            data["matrix"][m][s] = {}
            for d in DIRECTIONS:
                clip_list = matrix[m][s][d]
                data["matrix"][m][s][d] = {
                    "count": len(clip_list),
                    "knn_ready": len(clip_list) >= KNN_READY_THRESHOLD,
                    "clips": [c["clip_id"] for c in clip_list],
                }
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="PeakFlow Reference Library Coverage Report")
    parser.add_argument("--gaps-only", action="store_true", help="Only show missing combinations")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--reference-dir", type=Path, default=settings.REFERENCE_DIR)
    args = parser.parse_args()

    manifest = load_manifest(args.reference_dir)
    clips = manifest.get("clips", [])
    matrix = build_coverage_matrix(clips)

    if args.json:
        output_json(matrix, clips)
        return 0

    print(f"\n{'='*60}")
    print(f"  PeakFlow Reference Library Coverage Report")
    print(f"{'='*60}")

    if args.gaps_only:
        print_gaps_only(matrix)
    else:
        print_coverage_table(matrix)
        print_summary(matrix, clips)

    print(f"\n{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
