# MEMORY.md - PeakFlow (SURF) Project Documentation

> AI-powered surf video analysis engine with coaching feedback

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Directory Structure](#directory-structure)
5. [Data Models & Schemas](#data-models--schemas)
6. [Pipeline Stages](#pipeline-stages)
7. [API Endpoints](#api-endpoints)
8. [Configuration](#configuration)
9. [Design Decisions](#design-decisions)
10. [Development Guide](#development-guide)
11. [Current Status & TODOs](#current-status--todos)

---

## Project Overview

**Project Name:** PeakFlow
**Repository Name:** SURF
**Version:** 0.1.0
**Python:** >=3.10

### Purpose

Automate surf coaching by analyzing user videos through a sophisticated 6-stage pipeline. Users upload a video of their surf maneuver, get compared to pro references, and receive actionable tips to improve.

### Core Value Proposition

- Upload a surf maneuver video (3-15 seconds)
- AI extracts pose data and analyzes technique
- Matches against pro reference library
- Generates personalized coaching feedback via Claude AI

---

## Architecture

### High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER VIDEO INPUT                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Quality Gating                                            │
│  - Duration check (3-15 sec)                                        │
│  - Resolution check (min 480p)                                      │
│  - FPS check (min 24fps)                                            │
│  ❌ Reject poor videos early (fail-fast)                            │
└─────────────────────────────────────────────────────────────────────┘
                                │ ✓ Pass
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Context Detection                                         │
│  - Stance detection (regular/goofy)                                 │
│  - Direction detection (frontside/backside)                         │
│  - Wave direction detection                                         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Pose Extraction                                           │
│  - YOLO person detection                                            │
│  - SORT tracking (maintain identity)                                │
│  - MediaPipe 33-point pose landmarks                                │
│  - Trajectory smoothing (Savitzky-Golay)                            │
│  - Camera angle validation                                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Reference Matching                                        │
│  - Compute statistical embeddings                                   │
│  - Filter by stance/direction                                       │
│  - KNN matching (k=3, cosine similarity)                            │
│  - Return top-3 pro references                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 5: DTW Alignment                                             │
│  - Extract 7 key joint features                                     │
│  - Attention-weighted Dynamic Time Warping                          │
│  - Compute deviation metrics per joint/phase                        │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 6: Feedback Generation                                       │
│  - Send analysis to Claude API                                      │
│  - Generate 4-part coaching feedback                                │
│  - Fallback to rule-based if API unavailable                        │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ANALYSIS RESULT                                │
│  - Gating results                                                   │
│  - Context (stance, direction)                                      │
│  - Pose sequence                                                    │
│  - Matched references                                               │
│  - Deviation analysis                                               │
│  - Coaching feedback (what/why/drill/cue)                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Architectural Patterns

| Pattern | Usage |
|---------|-------|
| **Pipeline Pattern** | Sequential stages with early exit on failure |
| **Lazy Loading** | YOLO/MediaPipe models loaded on first use |
| **Dependency Injection** | FastAPI `Depends()` for orchestrator |
| **Singleton** | LRU cache for orchestrator instance |
| **Fail-Fast** | Invalid videos rejected early |

---

## Technology Stack

### Core Dependencies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Web Framework** | FastAPI | >=0.100.0 | REST API |
| **Server** | Uvicorn | >=0.23.0 | ASGI server |
| **Validation** | Pydantic | >=2.0.0 | Data models |
| **Computer Vision** | OpenCV | >=4.8.0 | Video processing |
| **Person Detection** | YOLO v8 (ultralytics) | >=8.0.0 | Detect surfer in frame |
| **Pose Estimation** | MediaPipe | >=0.10.0 | 33-point landmarks |
| **ML** | scikit-learn | >=1.3.0 | KNN matching |
| **Time Series** | tslearn | >=0.6.0 | DTW utilities |
| **LLM** | Anthropic SDK | >=0.18.0 | Claude API |
| **Numerical** | NumPy | >=1.24.0 | Array operations |
| **Signal Processing** | SciPy | >=1.10.0 | Smoothing filters |

### Dev Dependencies

- pytest (>=7.0.0)
- pytest-asyncio (>=0.21.0)
- httpx (>=0.24.0)
- ruff (linting)

---

## Directory Structure

```
SURF/
├── src/peakflow/                    # Main source code
│   ├── __init__.py
│   ├── config.py                    # Settings & configuration
│   │
│   ├── api/                         # FastAPI application
│   │   ├── main.py                  # App initialization & run
│   │   ├── routes.py                # API endpoints
│   │   └── dependencies.py          # DI (orchestrator)
│   │
│   ├── models/                      # Data models
│   │   ├── schemas.py               # Pydantic models (36 classes)
│   │   └── enums.py                 # Stance, Direction, Phase, etc.
│   │
│   ├── pipeline/                    # Analysis pipeline
│   │   ├── orchestrator.py          # Pipeline coordinator
│   │   ├── stage1_gating.py         # Quality validation
│   │   ├── stage2_context.py        # Stance/direction detection
│   │   ├── stage3_pose.py           # Pose extraction
│   │   ├── stage4_matching.py       # Reference matching
│   │   ├── stage5_dtw.py            # DTW alignment
│   │   └── stage6_feedback.py       # Feedback generation
│   │
│   ├── core/                        # Core utilities (placeholder)
│   ├── feedback/                    # Feedback utilities (placeholder)
│   └── reference/                   # Reference library management
│
├── data/                            # Data directory
│   └── references/
│       ├── manifest.json            # Reference metadata
│       ├── clips/                   # Pro video clips (.gitignore)
│       ├── poses/                   # Extracted poses (.gitignore)
│       └── embeddings/              # Pre-computed embeddings (.gitignore)
│
├── tests/                           # Test suite
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_gating.py               # Stage 1 tests
│   ├── test_pose.py                 # Stage 3 tests
│   └── test_dtw.py                  # Stage 5 tests
│
├── notebooks/                       # Jupyter notebooks (empty)
├── scripts/                         # Utility scripts
│   └── process_reference.py         # Reference clip processing CLI
│
├── pyproject.toml                   # Project configuration
├── requirements.txt                 # Pip requirements
├── README.md                        # Project README
├── MEMORY.md                        # This file
├── .env.example                     # Environment template
├── .env                             # Environment variables
└── .gitignore                       # Git ignore rules
```

---

## Data Models & Schemas

### Enums (`models/enums.py`)

```python
Stance: REGULAR | GOOFY | UNKNOWN
Direction: FRONTSIDE | BACKSIDE | UNKNOWN
ManeuverType: BOTTOM_TURN | CUTBACK | TOP_TURN
Phase: ENTRY | LOADING | DRIVE | EXIT
RejectionReason: TOO_SHORT | TOO_LONG | LOW_RESOLUTION | LOW_FPS |
                 NO_PERSON | MULTIPLE_PEOPLE | HEAD_ON_ANGLE |
                 FROM_BEHIND_ANGLE | LOW_POSE_CONFIDENCE
```

### Key Schemas (`models/schemas.py`)

| Schema | Purpose |
|--------|---------|
| `VideoMetadata` | Duration, resolution, FPS, frame count |
| `GatingResult` | Pass/fail with rejection reason |
| `ContextResult` | Stance, direction, wave direction, confidence |
| `PoseLandmark` | Single joint (x, y, z, visibility) |
| `FramePose` | Pose for one frame (33 landmarks) |
| `PoseSequence` | Full video pose data |
| `ReferenceClip` | Pro clip metadata |
| `MatchResult` | Top-K matched references |
| `JointDeviation` | Metrics for single joint |
| `AlignmentResult` | DTW path and costs |
| `DeviationAnalysis` | Full deviation report |
| `FeedbackResult` | 4-part coaching feedback |
| `AnalysisResult` | Complete pipeline output |

### Data Storage

**No traditional database.** Data stored as:
- JSON manifests (reference metadata)
- NumPy files (.npy) for poses and embeddings
- Video files (MP4, MOV, AVI, WebM)

---

## Pipeline Stages

### Stage 1: Quality Gating (`stage1_gating.py`)

**Purpose:** Reject unsuitable videos early to save processing.

**Checks:**
| Check | Requirement | Rejection Reason |
|-------|-------------|------------------|
| Duration | 3-15 seconds | `TOO_SHORT` / `TOO_LONG` |
| Resolution | Min 480p | `LOW_RESOLUTION` |
| Frame Rate | Min 24 fps | `LOW_FPS` |

**Output:** `GatingResult` with `VideoMetadata`

---

### Stage 2: Context Detection (`stage2_context.py`)

**Purpose:** Determine surfer's stance and direction.

**Detection Methods:**
- **Stance:** Analyze ankle positions (which foot forward)
- **Direction:** Shoulder-hip cross product (facing wave or away)
- **Wave Direction:** Hip center movement over time

**Output:** `ContextResult` with confidence score

---

### Stage 3: Pose Extraction (`stage3_pose.py`)

**Purpose:** Extract pose landmarks from video frames.

**Pipeline:**
1. **YOLO Detection:** Find person bounding boxes
2. **SORT Tracking:** Maintain identity across frames
3. **MediaPipe Pose:** Extract 33-point landmarks
4. **Smoothing:** Savitzky-Golay filter (window=5)
5. **Camera Angle Check:** Reject head-on/behind views

**MediaPipe Landmarks (33 points):**
- Face: nose, eyes, ears, mouth
- Upper body: shoulders, elbows, wrists
- Core: hips
- Lower body: knees, ankles, heels, toes

**Rejection Reasons:**
- `NO_PERSON`: No surfer detected
- `MULTIPLE_PEOPLE`: More than one person
- `HEAD_ON_ANGLE`: Camera facing surfer directly
- `FROM_BEHIND_ANGLE`: Camera behind surfer
- `LOW_POSE_CONFIDENCE`: Unreliable pose detection

**Output:** `PoseSequence` with frames, fps, duration

---

### Stage 4: Reference Matching (`stage4_matching.py`)

**Purpose:** Find similar pro clips for comparison.

**Process:**
1. Compute statistical embeddings (mean, std, range of joint angles)
2. Filter references by stance and direction
3. KNN matching (k=3) with cosine similarity
4. Return top-3 matches with similarity scores

**Output:** `MatchResult` with references and style cluster

---

### Stage 5: DTW Alignment (`stage5_dtw.py`)

**Purpose:** Align user and pro sequences, compute deviations.

**Key Features Extracted (7):**
```python
DTW_FEATURES = [
    "knee_flexion_back",      # Back knee bend
    "knee_flexion_front",     # Front knee bend
    "hip_flexion",            # Hip bend angle
    "torso_lean",             # Upper body lean
    "arm_elevation_leading",  # Leading arm height
    "arm_elevation_trailing", # Trailing arm height
    "compression_index",      # Overall body compression
]
```

**Attention Weights:**
```python
DTW_ATTENTION_WEIGHTS = {
    "knee_flexion_back": 1.0,      # Most important
    "knee_flexion_front": 0.8,
    "hip_flexion": 0.9,
    "torso_lean": 0.7,
    "arm_elevation_leading": 0.5,
    "arm_elevation_trailing": 0.5,
    "compression_index": 1.0,      # Most important
}
```

**DTW Algorithm:**
- Attention-weighted Euclidean distance
- Standard DTW with cumulative cost matrix
- Backtracking for alignment path
- Phase-wise deviation analysis

**Output:** `DeviationAnalysis` with primary error, severity, phase

---

### Stage 6: Feedback Generation (`stage6_feedback.py`)

**Purpose:** Generate human-readable coaching feedback.

**LLM Configuration:**
- Model: `claude-sonnet-4-20250514`
- Max tokens: 1024

**Feedback Format (4 parts):**
1. **What to Fix:** Specific technique issue
2. **Why It Matters:** Biomechanical explanation
3. **Dry Land Drill:** Practice exercise
4. **In-Water Cue:** Short mental cue for surfing

**Fallback:** Rule-based feedback if API unavailable

**Output:** `FeedbackResult`

---

## API Endpoints

**Base URL:** `http://localhost:8000`
**API Prefix:** `/api/v1`

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/analyze` | Full 6-stage analysis |
| `POST` | `/api/v1/validate` | Quick validation (gating only) |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/config` | Get configuration |

### Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### POST /api/v1/analyze

**Request:**
```
Content-Type: multipart/form-data
Body: video file (MP4, MOV, AVI, WebM)
Max size: 100MB
```

**Response:**
```json
{
  "video_path": "/tmp/tmpXXX.mp4",
  "gating": { ... },
  "context": { ... },
  "pose_sequence": { ... },
  "match": { ... },
  "deviation": { ... },
  "feedback": {
    "what_to_fix": "...",
    "why_it_matters": "...",
    "dry_land_drill": "...",
    "in_water_cue": "..."
  },
  "processing_time_ms": 3420
}
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (with defaults)
DATA_DIR=./data
REFERENCE_DIR=./data/references
API_HOST=0.0.0.0
API_PORT=8000
```

### Settings (`config.py`)

**Video Constraints:**
```python
MIN_DURATION_SEC = 3.0
MAX_DURATION_SEC = 15.0
MIN_RESOLUTION = 480
MIN_FPS = 24.0
```

**Model Settings:**
```python
YOLO_MODEL = "yolov8n.pt"  # Nano model for speed
YOLO_CONFIDENCE = 0.5
TRACKING_MAX_AGE = 30  # frames
```

**Pose Settings:**
```python
POSE_MIN_CONFIDENCE = 0.5
POSE_SMOOTHING_WINDOW = 5
MAX_JOINT_SPEED_M_S = 5.0
```

**Camera Angle Thresholds:**
```python
SHOULDER_HIP_RATIO_HEAD_ON = 1.5
SHOULDER_HIP_RATIO_FROM_BEHIND = 0.7
```

**Reference Matching:**
```python
N_REFERENCE_CLUSTERS = 3
TOP_K_REFERENCES = 3
```

**API:**
```python
MAX_UPLOAD_SIZE_MB = 100
```

---

## Design Decisions

### Why Pipeline Architecture?

**Decision:** Sequential 6-stage pipeline with fail-fast design.

**Rationale:**
- Early rejection saves expensive processing (YOLO, MediaPipe)
- Each stage is independent and testable
- Clear debugging: know exactly which stage failed
- Easy to add/modify stages

### Why No Database?

**Decision:** In-memory processing, JSON/NumPy file storage.

**Rationale:**
- Stateless API design for horizontal scaling
- Video analysis is inherently stateless
- Reference data is small enough for file-based storage
- Simplifies deployment (no DB setup)

### Why YOLO + MediaPipe?

**Decision:** YOLO for detection, MediaPipe for pose.

**Rationale:**
- YOLO excels at person detection (handles occlusion, multiple people)
- MediaPipe provides accurate 33-point pose landmarks
- Both are well-optimized for real-time performance
- Industry standard combination

### Why DTW over Other Methods?

**Decision:** Dynamic Time Warping for sequence alignment.

**Rationale:**
- Handles different video lengths naturally
- Robust to speed variations in maneuvers
- Attention weights allow domain knowledge injection
- Well-established in sports analytics

### Why View-Invariant Features?

**Decision:** Use joint angles instead of pixel coordinates.

**Rationale:**
- Camera distance/angle independence
- More meaningful for coaching ("knee angle" vs "pixel position")
- Better generalization across reference videos
- Stance-aware mapping (left/right → back/front)

### Why Claude for Feedback?

**Decision:** Claude API for generating coaching feedback.

**Rationale:**
- Natural language coaching is more actionable
- Can incorporate context (stance, maneuver type, phase)
- Structured 4-part format (what/why/drill/cue)
- Fallback to rules if API unavailable

### Why Lazy Model Loading?

**Decision:** Load YOLO/MediaPipe on first use.

**Rationale:**
- Faster API startup
- Lower memory when idle
- Models stay loaded after first request
- Better resource utilization

---

## Development Guide

### Setup

```bash
# Clone and install
cd SURF
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"

# Set environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

### Running

```bash
# Run API server
python -m peakflow.api.main

# Or with hot reload
uvicorn peakflow.api.main:app --reload

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=peakflow

# Specific test file
pytest tests/test_dtw.py -v
```

### Code Style

- **Linter:** Ruff
- **Line length:** 100 characters
- **Python target:** 3.10
- **Type hints:** Throughout codebase

### Reference Processing Script

The `scripts/process_reference.py` script manages the pro reference library.

**Add a new reference clip:**
```bash
python scripts/process_reference.py add \
  --video path/to/clip.mp4 \
  --surfer "Gabriel Medina" \
  --maneuver bottom_turn \
  --stance regular \
  --direction frontside \
  --style power,vertical \
  --source "WSL Highlights 2023" \
  --quality 5
```

**List all references:**
```bash
python scripts/process_reference.py list
```

**Remove a reference:**
```bash
python scripts/process_reference.py remove --id bt_regular_fs_power_001
```

**Processing Pipeline:**
1. Validates video passes quality gating
2. Copies video to `data/references/clips/{clip_id}.mp4`
3. Extracts poses using YOLO + MediaPipe → `data/references/poses/{clip_id}.npy`
4. Computes embedding → `data/references/embeddings/{clip_id}.npy`
5. Updates `manifest.json` with full metadata

**Clip ID Format:** `{maneuver_abbrev}_{stance}_{direction}_{style}_{counter:03d}`
- Example: `bt_regular_fs_power_001`
- Maneuver abbreviations: `bt` (bottom_turn), `cb` (cutback), `tt` (top_turn)

---

## Current Status & TODOs

### Completed

- [x] Full 6-stage pipeline implementation
- [x] FastAPI REST API
- [x] Pydantic data models (36 schemas)
- [x] Quality gating with rejection reasons
- [x] Context detection (stance, direction)
- [x] Pose extraction with YOLO + MediaPipe
- [x] Reference matching with KNN
- [x] DTW alignment with attention weights
- [x] Claude feedback generation
- [x] Unit tests for core stages
- [x] Configuration management
- [x] Reference clip processing script (`scripts/process_reference.py`)
- [x] Pro reference library with Gabriel Medina clip
- [x] End-to-end demo with amateur vs pro comparison

### Pending / Future Work

- [ ] **Frontend integration** - Build UI for video upload and results
- [ ] **Performance optimization** - Profile and optimize slow stages
- [ ] **GPU acceleration** - CUDA support for YOLO/MediaPipe
- [ ] **Batch processing** - Process multiple videos
- [ ] **User accounts** - Track progress over time
- [ ] **More maneuver types** - Expand beyond bottom turn/cutback
- [ ] **Mobile optimization** - Handle phone-recorded videos

### Known Limitations

1. **No frontend** - API-only, needs UI
2. **Single surfer only** - Rejects videos with multiple people
3. **Side angle required** - Rejects head-on and behind views
4. **3-15 second limit** - Videos outside range rejected

---

## Changelog

### v0.2.0 (Working Demo)

- Added reference clip processing CLI (`scripts/process_reference.py`)
- Populated reference library with pro surfer clips
- Fixed manifest loading for "clips" format
- End-to-end analysis pipeline fully functional
- Coaching feedback generation with Claude API

### v0.1.0 (Initial Release)

- Complete 6-stage pipeline
- FastAPI REST API
- Quality gating with fail-fast
- Pose extraction with YOLO + MediaPipe
- DTW alignment with attention weights
- Claude feedback generation
- Basic test suite

---

*Last updated: 2026-02-02*