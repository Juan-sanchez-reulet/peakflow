#!/usr/bin/env python3
"""
Download pro surf highlight reels from YouTube for the reference library.

Usage:
    python scripts/download_highlights.py add --url "https://youtube.com/watch?v=..." --name "wsl_pipe_2024"
    python scripts/download_highlights.py add --batch urls.txt
    python scripts/download_highlights.py list
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = settings.DATA_DIR / "downloads"
INDEX_FILE = DOWNLOADS_DIR / "index.json"


def check_dependencies():
    """Check that yt-dlp and ffmpeg are installed."""
    missing = []
    for tool in ["yt-dlp", "ffmpeg"]:
        if not shutil.which(tool):
            missing.append(tool)

    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Install with: brew install yt-dlp ffmpeg")
        return False
    return True


def load_index() -> dict:
    """Load download index."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {"downloads": []}


def save_index(index: dict) -> None:
    """Save download index."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)


def get_video_info(url: str) -> dict:
    """Get video metadata from URL using yt-dlp."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "resolution": f"{info.get('width', '?')}x{info.get('height', '?')}",
                "uploader": info.get("uploader", "Unknown"),
            }
    except Exception as e:
        logger.warning(f"Could not fetch video info: {e}")
    return {}


def download_video(url: str, name: str) -> bool:
    """Download a video using yt-dlp."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DOWNLOADS_DIR / f"{name}.mp4"

    if output_path.exists():
        logger.warning(f"File already exists: {output_path}")
        return True

    logger.info(f"Downloading: {name}")
    logger.info(f"URL: {url}")

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        url,
    ]

    try:
        result = subprocess.run(cmd, timeout=600)
        if result.returncode == 0 and output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Downloaded: {output_path} ({file_size_mb:.1f} MB)")

            # Update index
            info = get_video_info(url)
            index = load_index()
            index["downloads"].append({
                "name": name,
                "url": url,
                "file": f"{name}.mp4",
                "size_mb": round(file_size_mb, 1),
                "title": info.get("title", ""),
                "duration_sec": info.get("duration", 0),
                "resolution": info.get("resolution", ""),
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            })
            save_index(index)
            return True
        else:
            logger.error(f"Download failed (exit code {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Download timed out (10 min limit)")
        return False
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False


def add_videos(args):
    """Add one or more videos to download."""
    if not check_dependencies():
        return 1

    if args.batch:
        # Read URLs from file
        batch_file = Path(args.batch)
        if not batch_file.exists():
            logger.error(f"Batch file not found: {batch_file}")
            return 1

        lines = batch_file.read_text().strip().split("\n")
        success_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            url = parts[0]
            name = parts[1] if len(parts) > 1 else f"highlight_{i+1:03d}"
            if download_video(url, name):
                success_count += 1

        logger.info(f"Downloaded {success_count}/{len(lines)} videos")
        return 0

    # Single URL
    if not args.url:
        logger.error("Must provide --url or --batch")
        return 1

    name = args.name or f"highlight_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    success = download_video(args.url, name)
    return 0 if success else 1


def list_downloads(args):
    """List all downloaded videos."""
    index = load_index()
    downloads = index.get("downloads", [])

    if not downloads:
        print("\nNo downloads yet.")
        print(f"Download directory: {DOWNLOADS_DIR}")
        return 0

    print(f"\nDownloaded Highlights ({len(downloads)} videos)")
    print("=" * 80)

    for dl in downloads:
        print(
            f"\n  {dl['name']}"
            f"\n    File:     {dl.get('file', 'N/A')}"
            f"\n    Size:     {dl.get('size_mb', '?')} MB"
            f"\n    Duration: {dl.get('duration_sec', '?')}s"
            f"\n    Title:    {dl.get('title', 'N/A')}"
            f"\n    URL:      {dl.get('url', 'N/A')}"
        )

    print("\n" + "=" * 80)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PeakFlow Highlight Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a single video
  python scripts/download_highlights.py add --url "https://youtube.com/watch?v=XXX" --name "wsl_pipe_2024"

  # Download from a batch file (one URL per line, optionally followed by name)
  python scripts/download_highlights.py add --batch urls.txt

  # List all downloads
  python scripts/download_highlights.py list
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    add_p = subparsers.add_parser("add", help="Download a highlight reel")
    add_p.add_argument("--url", help="YouTube URL")
    add_p.add_argument("--name", help="Name for the download (without extension)")
    add_p.add_argument("--batch", help="Path to file with URLs (one per line)")

    subparsers.add_parser("list", help="List downloaded videos")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "add":
        return add_videos(args)
    elif args.command == "list":
        return list_downloads(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
