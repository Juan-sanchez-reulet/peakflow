# PeakFlow Frontend - Quick Start Guide

Get up and running in 2 minutes!

## Step 1: Install Dependencies (First Time Only)

```bash
cd /Users/lucassanchez/Desktop/code/SURF/frontend
npm install
```

This will take 1-2 minutes to download all packages (~150MB).

---

## Step 2: Start the Backend

Open Terminal 1:

```bash
cd /Users/lucassanchez/Desktop/code/SURF
source .venv/bin/activate
uvicorn peakflow.api.main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ Backend is ready when you see these messages.

**Test it**: Open http://localhost:8000/api/v1/health in your browser.
Should see: `{"status":"healthy","version":"0.1.0"}`

---

## Step 3: Start the Frontend

Open Terminal 2:

```bash
cd /Users/lucassanchez/Desktop/code/SURF/frontend
npm run dev
```

**Expected Output**:
```
  VITE v5.1.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

✅ Frontend is ready!

---

## Step 4: Open in Browser

Navigate to: **http://localhost:5173**

You should see:
- 🎨 Dark theme UI with gradient logo "PeakFlow"
- 🟢 Green dot in header (API Connected)
- 📤 Upload zone with drag-and-drop prompt

---

## Step 5: Test with a Video

### Option A: Drag & Drop
1. Open `/Users/lucassanchez/Desktop/code/SURF/data/test_clips/` in Finder
2. Drag any `.mp4` video onto the upload zone

### Option B: Click to Browse
1. Click the upload zone
2. Navigate to test_clips folder
3. Select a video

**What Happens Next**:
- ✅ Video preview appears
- ✅ Metadata shows (duration, resolution, fps, size)
- ✅ 5 validation checkmarks appear
- ✅ Blue "Analyze My Surf" button appears

---

## Step 6: Analyze!

1. Click **"Analyze My Surf"** button
2. Processing overlay appears (5-10 seconds)
3. Watch the stages progress:
   - Stage 1/6: Quality Gating ✓
   - Stage 2/6: Pose Extraction ✓
   - Stage 3/6: Context Detection ✓
   - Stage 4/6: Reference Matching ✓
   - Stage 5/6: DTW Alignment ✓
   - Stage 6/6: Feedback Generation ✓
4. Results appear in sidebar!

**Results Include**:
- 🎯 **Coaching Feedback** - What to fix, why it matters, drills, cues
- 🏄 **Context** - Stance (regular/goofy), direction (frontside/backside)
- 🏆 **Pro Comparison** - Matched to a professional surfer
- 📊 **Biomechanics** - Deviation analysis with severity gauge

---

## Troubleshooting

### Problem: API Offline (Red Dot)
**Solution**: Make sure backend is running in Terminal 1.

### Problem: "Network Error"
**Solution**:
```bash
# Check backend is responding
curl http://localhost:8000/api/v1/health
```

### Problem: Page won't load
**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Problem: Video validation fails
**Solution**: Make sure video is:
- 3-15 seconds long
- <100MB
- MP4, MOV, AVI, or WebM format
- Side angle (not head-on)

---

## Stopping the Servers

**Frontend** (Terminal 2): Press `Ctrl+C`

**Backend** (Terminal 1): Press `Ctrl+C`

---

## Next Session

When you come back:

```bash
# Terminal 1 - Backend
cd /Users/lucassanchez/Desktop/code/SURF
source .venv/bin/activate
uvicorn peakflow.api.main:app --reload

# Terminal 2 - Frontend
cd /Users/lucassanchez/Desktop/code/SURF/frontend
npm run dev
```

That's it! Both servers will start in ~5 seconds.

---

## Test Videos Location

Good videos to test with:
```
/Users/lucassanchez/Desktop/code/SURF/data/test_clips/
```

Look for videos that are:
- 3-15 seconds
- Side camera angle
- Single surfer visible
- Good lighting

---

## File Structure Reference

```
frontend/
├── src/
│   ├── components/          # All React components
│   ├── api/                 # API client, types, hooks
│   ├── store/               # State management (Zustand)
│   ├── utils/               # Validation, formatting
│   └── styles/              # Global CSS
├── public/                  # Static assets
├── index-react.html         # HTML entry point
├── package.json             # Dependencies
├── vite.config.ts           # Vite configuration
└── tailwind.config.js       # Styling configuration
```

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm install` | Install dependencies |

---

## What's Next?

1. ✅ Test with different videos
2. ✅ Try edge cases (too short, too long, etc.)
3. ✅ Test responsive design (resize browser)
4. ✅ Check TESTING.md for comprehensive test cases
5. 🚀 When ready: `npm run build` for production

---

## Need Help?

- 📖 **README.md** - Full documentation
- 🧪 **TESTING.md** - Comprehensive testing guide
- 💻 **Browser Console** - F12 to check for errors
- 📡 **Network Tab** - Monitor API calls

---

## Success Checklist

- [x] Backend running on http://localhost:8000
- [x] Frontend running on http://localhost:5173
- [x] Green "Connected" indicator in header
- [x] Can upload video
- [x] Validation checks appear
- [x] Can analyze video
- [x] Results display correctly

If all checked ✅ - **You're ready to surf! 🏄‍♂️**
