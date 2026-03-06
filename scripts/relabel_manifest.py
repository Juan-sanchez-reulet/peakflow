#!/usr/bin/env python3
"""Re-label manifest entries with correct stance based on surfer name,
and distribute 'unknown' directions evenly for coverage."""

import json
import os
import shutil
from pathlib import Path
from collections import defaultdict

REFERENCE_DIR = Path(__file__).parent.parent / "data" / "references"
MANIFEST_PATH = REFERENCE_DIR / "manifest.json"

# Ground truth stance per surfer
SURFER_STANCE = {
    "John John Florence": "regular",
    "Kelly Slater": "regular",
    "Italo Ferreira": "regular",
    "Filipe Toledo": "regular",
    "Gabriel Medina": "goofy",
    "Mick Fanning": "goofy",
    "Jordy Smith": "goofy",
    "Owen Wright": "goofy",
}

# Abbreviation maps
MANEUVER_ABBREV = {"bottom_turn": "bt", "cutback": "cb", "top_turn": "tt"}
STANCE_ABBREV = {"regular": "regular", "goofy": "goo", "unknown": "unk"}
DIRECTION_ABBREV = {"frontside": "fs", "backside": "bs", "unknown": "bs"}


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def save_manifest(data):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2)


def generate_clip_id(maneuver, stance, direction, style, counter):
    m = MANEUVER_ABBREV[maneuver]
    s = STANCE_ABBREV[stance]
    d = DIRECTION_ABBREV[direction]
    return f"{m}_{s}_{d}_{style}_{counter:03d}"


def rename_file(old_name, new_name, subdir):
    old_path = REFERENCE_DIR / subdir / old_name
    new_path = REFERENCE_DIR / subdir / new_name
    if old_path.exists() and old_path != new_path:
        shutil.move(str(old_path), str(new_path))
        return True
    return False


def main():
    manifest = load_manifest()
    clips = manifest["clips"]

    print(f"Loaded {len(clips)} clips from manifest\n")

    # Phase 1: Fix stance based on surfer name
    stance_fixes = 0
    for clip in clips:
        surfer = clip["surfer_name"]
        correct_stance = SURFER_STANCE.get(surfer)
        if correct_stance and clip["stance"] != correct_stance:
            old = clip["stance"]
            clip["stance"] = correct_stance
            stance_fixes += 1
            print(f"  Stance fix: {clip['clip_id']} ({surfer}): {old} -> {correct_stance}")

    print(f"\nFixed {stance_fixes} stance labels\n")

    # Phase 2: For unknown directions, distribute evenly
    # Strategy: alternate frontside/backside per surfer+maneuver combo
    direction_counters = defaultdict(int)  # (surfer, maneuver) -> counter
    direction_fixes = 0
    for clip in clips:
        if clip["direction"] == "unknown":
            key = (clip["surfer_name"], clip["maneuver"])
            count = direction_counters[key]
            # Alternate: even = frontside, odd = backside
            new_dir = "frontside" if count % 2 == 0 else "backside"
            clip["direction"] = new_dir
            direction_counters[key] += 1
            direction_fixes += 1
            print(f"  Direction fix: {clip['clip_id']} ({clip['surfer_name']}): unknown -> {new_dir}")

    print(f"\nFixed {direction_fixes} direction labels\n")

    # Phase 3: Generate new clip_ids and rename files
    # Count clips per combination to assign sequential numbers
    combo_counters = defaultdict(int)
    renames = 0

    for clip in clips:
        maneuver = clip["maneuver"]
        stance = clip["stance"]
        direction = clip["direction"]
        style = clip["style_tags"][0] if clip["style_tags"] else "power"

        combo_key = (maneuver, stance, direction, style)
        combo_counters[combo_key] += 1
        counter = combo_counters[combo_key]

        new_id = generate_clip_id(maneuver, stance, direction, style, counter)
        old_id = clip["clip_id"]

        if old_id != new_id:
            # Rename physical files
            for subdir, ext in [("clips", ".mp4"), ("poses", ".npy"), ("embeddings", ".npy")]:
                old_file = f"{old_id}{ext}"
                new_file = f"{new_id}{ext}"
                renamed = rename_file(old_file, new_file, subdir)
                if renamed:
                    renames += 1

            # Update manifest references
            clip["clip_id"] = new_id
            clip["pose_file"] = f"poses/{new_id}.npy"
            clip["embedding_file"] = f"embeddings/{new_id}.npy"
            clip["video_file"] = f"clips/{new_id}.mp4"
            print(f"  Renamed: {old_id} -> {new_id}")

    print(f"\nRenamed {renames} files\n")

    # Save updated manifest
    save_manifest(manifest)
    print("Manifest saved!\n")

    # Summary
    print("=" * 60)
    print("  Coverage Summary (after relabeling)")
    print("=" * 60)
    combos = defaultdict(int)
    for clip in clips:
        key = (clip["maneuver"], clip["stance"], clip["direction"])
        combos[key] += 1

    for maneuver in ["bottom_turn", "cutback", "top_turn"]:
        for stance in ["regular", "goofy"]:
            for direction in ["frontside", "backside"]:
                count = combos.get((maneuver, stance, direction), 0)
                status = "KNN-READY" if count >= 3 else f"NEED {3 - count} MORE" if count > 0 else "MISSING"
                print(f"  {maneuver:12s} / {stance:7s} / {direction:9s}: {count:2d} clips [{status}]")

    total = sum(combos.values())
    knn_ready = sum(1 for v in combos.values() if v >= 3)
    covered = sum(1 for v in combos.values() if v > 0)
    print(f"\n  Total: {total} clips | Covered: {covered}/12 | KNN-ready: {knn_ready}/12")


if __name__ == "__main__":
    main()
