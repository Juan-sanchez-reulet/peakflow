# PeakFlow

Surf video analysis engine that compares a surfer's biomechanics against a pro reference library and generates coaching feedback.

## Overview

PeakFlow takes a short video of a surf maneuver, runs it through a 6-stage computer vision pipeline, and produces structured coaching feedback grounded in how the surfer's body mechanics deviate from a matched professional reference. The output is not a score — it is a specific correction, the reason it matters, how a matched pro handles that phase differently, a dry-land drill, and a 5-word cue to think about in the water.

The pipeline is designed around a hard constraint: pose estimation on surfing footage is noisy. Surfers move fast, video is often shot from a distance, and consumer cameras introduce frame drop and codec artifacts. Each stage filters out inputs that would produce unreliable analysis before any expensive computation runs. The system rejects a video with a useful message rather than producing a confident result on bad data.

The DTW alignment in Stage 5 compares a feature sequence extracted from the user's clip against the best-matched pro reference frame by frame, accounting for differences in speed and timing. This makes it possible to identify where in the maneuver the deviation is largest and which joint is responsible, which gives the LLM feedback generator in Stage 6 something precise to work from instead of a vague similarity score.

## Pipeline

**Stage 1 — Quality Gating**

OpenCV extracts metadata before any model runs. Checks run in order of cost: duration (must be 3–15 seconds), resolution (minimum 480p on the short side), and frame rate (minimum 24 fps). The pipeline returns immediately on the first failure with a message that tells the user exactly what to change. Videos outside these bounds will produce unreliable pose sequences because MediaPipe needs enough temporal resolution and visual information to track joints accurately.

**Stage 2 — Context Detection**

Determines stance (regular or goofy) and turn direction (frontside or backside) from the pose sequence. Stance is inferred from which ankle is consistently further forward in image x-coordinates across the middle 50% of frames — using the full sequence would include the approach and exit where foot position is ambiguous. Direction is inferred from the cross product of the shoulder vector and hip vector, with the sign inverted for goofy stance because the body geometry is mirrored. Wave direction (left-to-right vs. right-to-left) is detected from hip center displacement between the first and last sampled frames. These three values are required to filter the reference library before matching — comparing a goofy backside turn against a regular frontside reference would produce meaningless deviations.

**Stage 3 — Pose Extraction**

YOLOv8n detects persons in each frame at 0.3 confidence. A simplified SORT-style tracker selects the largest bounding box to identify the primary surfer. The crop is expanded by 20% padding on each side before being passed to MediaPipe Pose at complexity level 2. Only frames with average landmark visibility above 0.5 are kept. After extraction, a Savitzky-Golay filter (window=5, polynomial order=2) smooths each landmark trajectory independently across the sequence. The filter is chosen over a simple moving average because it preserves the shape of peaks and troughs, which matters for DTW alignment where the timing and magnitude of extreme positions carry diagnostic information. Camera angle is validated after pose extraction by computing the shoulder-to-hip width ratio: above 2.0 indicates a head-on shot, below 0.5 indicates a from-behind shot. Both angles make stance-based biomechanical analysis unreliable and are rejected. If fewer than 10 frames pass confidence filtering, the video is rejected for insufficient pose data.

**Stage 4 — Reference Matching**

The user's pose sequence is compressed into a fixed-length statistical embedding: mean, standard deviation, and range of 5 joint angles across all frames, plus normalized peak timing positions for each angle. These 20 features are compared against pre-computed embeddings for the filtered reference clips using cosine KNN (scikit-learn `NearestNeighbors`). The reference library is filtered by stance, direction, and maneuver type before KNN runs so the search space is always biomechanically compatible. The top 3 matches are returned along with a style cluster derived from the majority style tag (`power` or `flow`) of the matched clips.

**Stage 5 — DTW Alignment**

Dynamic Time Warping aligns the user's feature sequence against the closest matched pro reference. The 7 features are: back knee flexion, front knee flexion, hip flexion, torso lean, trailing arm elevation, leading arm elevation, and compression index. Left/right landmarks are remapped to front/back based on detected stance so the same DTW logic applies to both regular and goofy surfers. Features are weighted before distance computation: back knee and compression index carry weight 1.0, hip flexion 0.9, front knee 0.8, torso lean 0.7, and arms 0.5. These weights reflect how much each joint contributes to power generation in a bottom turn. After alignment, the per-joint deviation at each step in the warping path is computed, and the joint with the largest attention-weighted maximum deviation becomes the primary error. The position of that maximum along the path classifies it into one of four maneuver phases: entry (0–25%), loading (25–50%), drive (50–75%), exit (75–100%).

**Stage 6 — Feedback Generation**

Claude (`claude-sonnet-4-6`, max 1024 tokens) receives the primary deviation, severity, phase, matched pro name, and qualitative observations about the top 3 joints. The prompt uses the Rob Machado powersurf methodology vocabulary and explicitly prohibits numerical outputs — the model is instructed to describe everything in surf language ("your back knee stays too straight", not "your knee angle deviates by 23 degrees"). The response is parsed into 6 fixed sections: **What We See**, **What to Fix**, **Why It Matters**, **Pro Insight**, **Dry-Land Drill**, and **In-Water Cue** (max 5 words). If the API is unavailable or the key is not set, a rule-based fallback generates the same 6 sections from a lookup table keyed by primary error type.

## Architecture decisions

DTW is used over cosine similarity or Euclidean distance on the full sequence because user clips vary in duration from 3 to 15 seconds and capture the maneuver at different speeds. A Euclidean comparison would penalize a surfer for doing a slower bottom turn even if the biomechanics are identical. DTW finds the optimal alignment between two sequences of different lengths and measures how far apart they are after alignment. The cost of the alignment is O(T1 × T2) which is acceptable because the sequences are short — at 24 fps a 15-second clip is 360 frames and the reference clips average around 68 frames, so the cost matrix stays manageable without windowing.

The pipeline runs two separate embedding strategies for the same pose data. Stage 4 uses a statistical embedding (mean, std, range, peak timing) to do fast approximate matching across the full library. This collapses the temporal dimension into a fixed-length vector so KNN can run cheaply. Stage 5 then operates on the full frame-by-frame feature sequence for the single best-matched reference. This separation avoids running DTW against all 54 clips on every request while still getting precise temporal deviation information for the winning match.

The ffmpeg re-encode step before any model inference is mandatory, not optional. Browser-recorded video, particularly from iOS, uses H264 High Profile which OpenCV cannot decode. The pipeline re-encodes every upload to H264 baseline with `yuv420p` pixel format before processing. Skipping this step would cause silent failures on a large fraction of real-world inputs with no indication to the user.

Attention weights for DTW are set by hand based on the biomechanics of a power bottom turn — back knee compression and overall compression index are the primary power sources, so they receive maximum weight. Arm position has less direct impact on rail pressure and receives half the weight. These weights are static constants in config and are a candidate for learning from labeled data if annotation ever becomes available.

## Reference library

The library contains 54 clips covering 3 maneuvers (bottom turn, cutback, top turn), 2 stances (regular, goofy), 2 directions (frontside, backside), and 2 style tags (power, flow). Surfers represented: Gabriel Medina, John John Florence, Kelly Slater, Italo Ferreira, Jordy Smith, Mick Fanning, Owen Wright. Clips are sourced from public WSL highlight footage.

For each clip the library stores two files:

`poses/<clip_id>.npy` — shape `(T, 33, 4)`. T is frame count, 33 is the number of MediaPipe Pose landmarks, and the last dimension is `[x, y, z, visibility]`. Coordinates are normalized to `[0, 1]` in image space. Z is depth relative to the hip midpoint, also normalized.

`embeddings/<clip_id>.npy` — shape `(20,)`. The statistical embedding computed by Stage 4: mean (5), std (5), range (5), and peak timing (5) of the 5 joint angles used for KNN matching.

The manifest (`data/references/manifest.json`) records clip metadata including surfer name, source event, stance, direction, maneuver, style tags, quality score (1–5), and paths to the pose and embedding files.

The reference clips and embeddings are not included in this repository due to size. See `scripts/process_reference.py` to process new reference clips from local video files, and `scripts/download_highlights.py` to download WSL source footage.

## Tech stack

**Backend**
- Python >=3.10
- FastAPI >=0.100.0 + uvicorn >=0.23.0
- MediaPipe >=0.10.0
- OpenCV >=4.8.0
- YOLOv8 via ultralytics >=8.0.0
- NumPy >=1.24.0
- SciPy >=1.10.0 (Savitzky-Golay filter)
- scikit-learn >=1.3.0 (KNN)
- tslearn >=0.6.0
- anthropic >=0.18.0
- Pydantic >=2.0.0 + pydantic-settings >=2.0.0
- python-multipart >=0.0.6

**Frontend**
- React 18.3.1 + TypeScript 5.3.3
- Vite 5.1.0
- Tailwind CSS 3.4.1
- Zustand 4.5.0
- TanStack Query 5.20.0
- Framer Motion 11.0.3
- Recharts 2.12.0
- Axios 1.6.7

**System dependency:** `ffmpeg` must be installed and on `PATH`.

## Setup

```bash
git clone <repo>
cd peakflow

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e .

cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY

# Frontend (optional — API works without it)
cd frontend
npm install
npm run build
cd ..

# Run
peakflow
# API available at http://localhost:8000
# Frontend (if built) served at http://localhost:8000
# API docs at http://localhost:8000/docs
```

Without a built frontend, the API runs standalone and accepts requests at `/api/v1/analyze`.

To process new reference clips into the library:

```bash
python scripts/process_reference.py --video path/to/clip.mp4 \
  --id bt_regular_fs_power_008 \
  --maneuver bottom_turn --stance regular \
  --direction frontside --surfer "Surname" \
  --source "Event Name" --style power
```

## Limitations

The current reference library is weighted toward bottom turns — most clips cover that maneuver. Cutback and top turn analysis will match against fewer references and produce less reliable comparisons.

Stance detection uses only the x-axis position of ankles. It fails predictably when the camera is positioned directly in front of or behind the surfer — which is also the condition the camera angle check is designed to catch and reject. If a video passes the angle check but still produces an incorrect stance detection, direction and all downstream analysis will be wrong in a way that is not surfaced to the user.

The SORT tracker is simplified to pick the largest bounding box in each frame. It is not a true multi-object tracker and has no re-identification across large gaps. If two surfers are visible and the target surfer is temporarily the smaller detection, the tracker will switch subjects.

MediaPipe runs at complexity level 2 (the most accurate setting). Full pipeline processing time is roughly 15–40 seconds on CPU for a 10-second clip. There is no GPU path and no batching — the pipeline processes one video at a time.

The LLM feedback focuses on a single primary error. Secondary deviations are passed as context but the prompt explicitly instructs the model to address only the main issue. This is intentional — multiple simultaneous corrections are hard to act on — but it means significant secondary problems may go unmentioned.

All analysis is currently limited to bottom turns. Uploading a cutback or top turn will run through the pipeline but will match against whatever bottom turn reference is closest in embedding space, producing feedback that is technically correct about the body mechanics shown but potentially not relevant to the intended maneuver.
