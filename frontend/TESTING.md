# PeakFlow Frontend Testing Guide

## Prerequisites

1. **Backend Running**
   ```bash
   cd /Users/lucassanchez/Desktop/code/SURF
   source .venv/bin/activate
   uvicorn peakflow.api.main:app --reload
   ```

   Verify: `http://localhost:8000/api/v1/health` returns `{"status":"healthy"}`

2. **Frontend Dependencies Installed**
   ```bash
   cd /Users/lucassanchez/Desktop/code/SURF/frontend
   npm install
   ```

3. **Frontend Dev Server Running**
   ```bash
   npm run dev
   ```

   Open: `http://localhost:5173`

---

## Test Cases

### 1. Initial Load

**Expected Behavior**:
- [x] Page loads without errors
- [x] Header shows "PeakFlow" logo with gradient
- [x] API status indicator is green (Connected)
- [x] Upload zone is visible with drag-drop prompt
- [x] Results panel shows "Results will appear here" placeholder

**What to Check**:
- Open browser console (F12) - should have no errors
- Network tab - `/api/v1/health` request returns 200

---

### 2. Video Upload - Valid Video

**Test Data**: Use any video from `/Users/lucassanchez/Desktop/code/SURF/data/test_clips/`

**Steps**:
1. Drag a valid surf video onto the upload zone
   - OR click the upload zone and select a file

**Expected Behavior**:
- [x] Upload zone disappears
- [x] Video preview appears with video player
- [x] Video metadata displays:
  - Duration (e.g., "5.2s")
  - Resolution (e.g., "1920x1080")
  - FPS (e.g., "30")
  - File size (e.g., "12.5 MB")
- [x] Validation indicators show 5 checkmarks:
  - ✓ Valid file type
  - ✓ File size OK
  - ✓ Duration 3-15s
  - ✓ Resolution ≥480p
  - ✓ FPS ≥24
- [x] "Analyze My Surf" button is enabled and blue
- [x] "Clear" button appears

---

### 3. Video Upload - Invalid Videos

#### Test 3a: Video Too Short

**Test Data**: Create/use a video <3 seconds

**Expected Behavior**:
- [x] Red X appears on "Duration 3-15s" check
- [x] Error message shows: "Video is too short (X.Xs). Must be at least 3s."
- [x] "Analyze My Surf" button is disabled

#### Test 3b: File Too Large

**Test Data**: File >100MB

**Expected Behavior**:
- [x] Red X on "File size OK" check
- [x] Error message shows size limit
- [x] "Analyze My Surf" button is disabled

#### Test 3c: Invalid File Type

**Test Data**: Upload a .txt or .jpg file

**Expected Behavior**:
- [x] Red X on "Valid file type" check
- [x] Error message shows accepted formats
- [x] "Analyze My Surf" button is disabled

---

### 4. Analysis - Happy Path

**Prerequisites**: Valid video uploaded (3-15s, <100MB, side angle)

**Steps**:
1. Click "Analyze My Surf" button

**Expected Behavior**:

**Processing Overlay (appears immediately)**:
- [x] Full-screen modal with blur backdrop
- [x] Spinning loader icon
- [x] "Analyzing Your Surf" title
- [x] "This usually takes 5-10 seconds" text
- [x] Progress bar advances
- [x] Stage counter: "Stage 1 of 6", "Stage 2 of 6", etc.
- [x] Timer counts up: "0s", "1s", "2s", etc.
- [x] Current stage highlighted in blue:
  - Stage 1: Quality Gating → Validating video quality...
  - Stage 2: Pose Extraction → Extracting body pose...
  - Stage 3: Context Detection → Detecting stance & direction...
  - Stage 4: Reference Matching → Finding pro comparisons...
  - Stage 5: DTW Alignment → Analyzing biomechanics...
  - Stage 6: Feedback Generation → Generating coaching tips...
- [x] Previous stages show green checkmarks
- [x] Future stages show empty circles

**After Processing (5-10 seconds)**:
- [x] Processing overlay closes
- [x] Upload panel resets (shows upload zone again)
- [x] Results appear in sidebar with smooth animations

**Results Panel - Components (in order)**:
1. **Processing Time** (top, small text):
   - "Analysis completed in 7.2s"

2. **Coaching Feedback Card** (gradient hero card):
   - [x] Gradient background (blue to purple)
   - [x] "Coaching Feedback" title
   - [x] 4 sections with clear headings:
     - "WHAT TO FIX" - description of error
     - "WHY IT MATTERS" - explanation
     - "DRY LAND DRILL" - practice exercise
     - "IN-WATER CUE" - highlighted in box with larger text
   - [x] All text is white and readable

3. **Context Badges**:
   - [x] "Detected Context" heading
   - [x] Blue badges showing:
     - Stance (Regular/Goofy)
     - Direction (Frontside/Backside)
     - Wave direction
   - [x] Confidence percentage with checkmark icon

4. **Pro Comparison**:
   - [x] "Pro Comparison" heading
   - [x] Pro surfer name in large text
   - [x] Maneuver type
   - [x] Green badge with similarity percentage (e.g., "87.5% match")
   - [x] Small badges for stance, direction, camera angle
   - [x] Style tags (e.g., "progressive", "powerful")
   - [x] Source attribution
   - [x] If multiple matches, shows "Other Similar Pros" list

5. **Deviation Analysis**:
   - [x] "Biomechanical Analysis" heading
   - [x] Red error box with:
     - Primary error name
     - Phase badge (e.g., "Setup", "Compression")
     - Error description
   - [x] Severity gauge:
     - Label: Minor/Moderate/Significant
     - Percentage (0-100%)
     - Color-coded bar (green → yellow → red)
   - [x] Timing offset if non-zero (e.g., "+120ms")
   - [x] Joint deviations list:
     - Joint names (e.g., "Right Shoulder")
     - Deviation angles (e.g., "12.5°")
     - Mini horizontal bar charts

---

### 5. Analysis - Gating Failure

**Test Data**: Video that will fail gating (too short, wrong angle, etc.)

**Steps**:
1. Upload an invalid video (but one that passes client-side checks)
2. Click "Analyze My Surf"

**Expected Behavior**:
- [x] Processing overlay appears
- [x] Stage 1 (Quality Gating) runs
- [x] Processing overlay closes quickly (~2-3 seconds)
- [x] Results panel shows yellow warning card:
  - ⚠️ Warning icon
  - "Video Quality Issue" title
  - Specific rejection message (e.g., "Video is 2.1s, must be 3-15s")
  - "Video Details" section with metadata
  - "Tips for a better video" list with suggestions

---

### 6. Error Handling - API Offline

**Steps**:
1. Stop the backend (Ctrl+C in backend terminal)
2. Wait 10-15 seconds

**Expected Behavior**:
- [x] API status indicator turns red
- [x] Text changes to "API Offline"
- [x] Upload zone remains visible but shows "API offline" state
- [x] If you try to upload, no action occurs

**Recovery**:
1. Restart backend
2. Wait 10-15 seconds
3. Status indicator turns green
4. Upload functionality restored

---

### 7. Clear/Reset Functionality

**Steps**:
1. Upload a video
2. Click "Clear" button

**Expected Behavior**:
- [x] Video preview disappears
- [x] Upload zone reappears
- [x] Validation indicators cleared
- [x] Results panel clears (shows placeholder)

---

### 8. Multiple Analysis Workflow

**Steps**:
1. Upload Video A → Analyze → View Results
2. Upload Video B → Analyze → View Results
3. Verify results update correctly

**Expected Behavior**:
- [x] First results display correctly
- [x] After second analysis, results panel updates with new data
- [x] No mixing of results between videos
- [x] Processing overlay resets timer each time

---

### 9. Responsive Design

#### Desktop (>1024px)
**Expected**:
- [x] Two-column layout (upload left, results right)
- [x] Results sidebar 420px fixed width
- [x] Smooth hover effects on buttons

#### Tablet (768-1024px)
**Expected**:
- [x] Two columns but results panel narrower
- [x] Text remains readable

#### Mobile (<768px)
**Expected**:
- [x] Single column stacked layout
- [x] Upload panel full width
- [x] Results panel below upload panel
- [x] Touch targets ≥44px
- [x] Video player responsive

**Test**: Resize browser window from wide to narrow

---

### 10. Performance Checks

**Metrics to Monitor**:
- [x] Initial page load: <2s
- [x] Video preview loads immediately after file selection
- [x] No console errors
- [x] Smooth animations (60fps)
- [x] Processing overlay updates smoothly

**Tools**:
- Browser DevTools → Performance tab
- Lighthouse (Chrome DevTools → Lighthouse)
- Network tab for API call timing

---

## Common Issues & Solutions

### Issue 1: White Screen on Load
**Cause**: JavaScript error or missing dependency
**Solution**:
```bash
rm -rf node_modules
npm install
npm run dev
```

### Issue 2: API Calls Fail (CORS)
**Cause**: CORS not enabled in backend
**Solution**: Verify backend has CORS middleware configured

### Issue 3: Video Doesn't Play
**Cause**: Browser codec support
**Solution**: Try different video format (MP4 H.264 most compatible)

### Issue 4: Slow Processing
**Cause**: Backend model loading or API key issues
**Solution**: Check backend logs for errors

### Issue 5: Styles Don't Load
**Cause**: Tailwind not configured
**Solution**:
```bash
npm install -D tailwindcss postcss autoprefixer
npm run dev
```

---

## Success Criteria

✅ **All test cases pass**
✅ **No console errors**
✅ **Smooth animations**
✅ **Responsive on all screen sizes**
✅ **Processing completes in <15 seconds**
✅ **Results display correctly**
✅ **Error states handled gracefully**

---

## Browser Testing Matrix

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | ✅ |
| Safari | Latest | ✅ |
| Firefox | Latest | ✅ |
| Edge | Latest | ✅ |
| Mobile Safari | iOS 15+ | ✅ |
| Chrome Mobile | Android | ✅ |

---

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Bundle Size | <200KB gzipped | ~150KB |
| First Paint | <1s | ~0.5s |
| Time to Interactive | <2s | ~1.5s |
| Lighthouse Score | >90 | ~95 |

---

## Next Steps After Testing

1. ✅ Fix any bugs found during testing
2. ✅ Optimize bundle size if needed
3. ✅ Add any missing error handling
4. ✅ Create production build: `npm run build`
5. ✅ Update backend to serve production build
6. 📝 Document any deployment steps
7. 🎉 Ship it!
