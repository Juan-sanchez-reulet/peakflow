# PeakFlow - Surf Video Analysis Engine

AI-powered surf video analysis with coaching feedback. Upload a video of your maneuver, get compared to pro references, and receive actionable tips to improve.

## Features

- **6-Stage Pipeline**: Quality gating → Context detection → Pose extraction → Reference matching → DTW alignment → Feedback generation
- **Intelligent Gating**: Rejects unusable videos early with helpful feedback
- **Pose Analysis**: MediaPipe-based pose extraction with YOLO person detection
- **Pro Comparison**: Dynamic Time Warping aligns your technique to pro references
- **AI Coaching**: Claude-powered feedback with drills and in-water cues

## Quick Start

### Installation

```bash
# Clone and navigate to project
cd peakflow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Anthropic API key
ANTHROPIC_API_KEY=your_api_key_here
```

### Run the API

```bash
# Start the server
python -m peakflow.api.main

# Or use uvicorn directly
uvicorn peakflow.api.main:app --reload
```

The API will be available at `http://localhost:8000`.
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### Analyze a Video

```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@your_surf_video.mp4"
```

Or use the interactive docs at `/docs` to upload a video.

## Project Structure

```
peakflow/
├── src/peakflow/
│   ├── pipeline/           # 6-stage analysis pipeline
│   │   ├── stage1_gating.py
│   │   ├── stage2_context.py
│   │   ├── stage3_pose.py
│   │   ├── stage4_matching.py
│   │   ├── stage5_dtw.py
│   │   ├── stage6_feedback.py
│   │   └── orchestrator.py
│   ├── models/             # Pydantic schemas
│   ├── api/                # FastAPI application
│   └── config.py           # Settings
├── data/
│   └── references/         # Pro reference library
├── tests/                  # Test suite
└── notebooks/              # Exploration notebooks
```

## Video Requirements

- **Duration**: 3-15 seconds
- **Resolution**: Minimum 480p
- **Frame Rate**: Minimum 24fps
- **Content**: Single surfer, filmed from the side (not head-on or from behind)
- **Format**: MP4, MOV, AVI, or WebM

## API Endpoints

### POST /api/v1/analyze

Full analysis of a surf video.

**Request**: `multipart/form-data` with `video` file

**Response**:
```json
{
  "video_path": "...",
  "gating": {
    "passed": true,
    "metadata": {...}
  },
  "context": {
    "stance": "regular",
    "direction": "frontside",
    "wave_direction": "left_to_right",
    "confidence": 0.85
  },
  "deviation": {
    "primary_error": "knee_flexion_back",
    "severity": 0.73,
    "phase": "loading",
    ...
  },
  "feedback": {
    "what_to_fix": "Your back knee isn't compressing enough...",
    "why_it_matters": "Without back knee compression...",
    "dry_land_drill": "Wall squats with focus on back leg...",
    "in_water_cue": "Knee to deck"
  },
  "processing_time_ms": 3420
}
```

### POST /api/v1/validate

Quick validation without full analysis.

### GET /api/v1/health

Health check endpoint.

### GET /api/v1/config

Get current configuration values.

## Development

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=peakflow
```

### Add Reference Clips

1. Add pro video clips to `data/references/clips/`
2. Run the processing script (coming soon):
   ```bash
   python scripts/process_reference.py
   ```
3. Update `data/references/manifest.json`

## Architecture

### Pipeline Stages

1. **Quality Gating** - Validates video meets requirements before processing
2. **Context Detection** - Detects stance (regular/goofy) and direction (frontside/backside)
3. **Pose Extraction** - YOLO detection + SORT tracking + MediaPipe pose estimation
4. **Reference Matching** - KNN matching to find similar pro clips
5. **DTW Alignment** - Attention-weighted Dynamic Time Warping for sequence comparison
6. **Feedback Generation** - Claude API generates coaching advice

### Key Technologies

- **MediaPipe**: Pose landmark detection
- **YOLO v8**: Person detection
- **scikit-learn**: KNN matching, embeddings
- **NumPy/SciPy**: DTW implementation
- **FastAPI**: REST API
- **Claude API**: Natural language feedback

## License

MIT
