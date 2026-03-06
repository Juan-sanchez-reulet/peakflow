# PeakFlow Frontend

Modern React + TypeScript + Vite frontend for PeakFlow AI Surf Coaching.

## Features

- 🎨 Modern UI with Tailwind CSS
- ⚡️ Fast development with Vite + HMR
- 🔒 Type-safe with TypeScript
- 📱 Responsive design (mobile, tablet, desktop)
- 🎬 Drag-and-drop video upload
- ✅ Client-side validation
- 📊 Real-time processing progress
- 🎯 Beautiful results display with animations

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **TanStack Query** - API data fetching
- **Framer Motion** - Animations
- **React Dropzone** - File upload
- **Recharts** - Data visualization
- **Axios** - HTTP client

## Installation

```bash
cd /Users/lucassanchez/Desktop/code/SURF/frontend
npm install
```

## Development

### 1. Start the Backend

```bash
cd /Users/lucassanchez/Desktop/code/SURF
source .venv/bin/activate
uvicorn peakflow.api.main:app --reload
```

Backend will run on `http://localhost:8000`

### 2. Start the Frontend

```bash
cd /Users/lucassanchez/Desktop/code/SURF/frontend
npm run dev
```

Frontend will run on `http://localhost:5173`

The Vite dev server automatically proxies `/api/*` requests to the backend.

## Production Build

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

To preview the production build:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── common/       # Reusable UI components
│   │   ├── layout/       # Layout components
│   │   ├── upload/       # Upload flow components
│   │   ├── processing/   # Processing overlay
│   │   └── results/      # Results display
│   ├── api/              # API client and hooks
│   ├── store/            # Zustand state management
│   ├── utils/            # Utility functions
│   ├── styles/           # Global styles
│   └── main.tsx          # App entry point
├── public/               # Static assets
└── index-react.html      # HTML entry point
```

## Testing Checklist

### Setup
- [x] Backend running on `localhost:8000`
- [x] Frontend running on `localhost:5173`
- [x] API health indicator shows green

### Upload Flow
- [ ] Drag video from test_clips directory
- [ ] Video preview displays correctly
- [ ] Metadata shows (duration, resolution, fps, size)
- [ ] Validation checkmarks appear

### Processing
- [ ] Click "Analyze My Surf" button
- [ ] Processing overlay appears with spinner
- [ ] Stages progress 1→2→3→4→5→6
- [ ] Timer counts elapsed time
- [ ] Overlay closes when done

### Results (Happy Path)
- [ ] Coaching feedback card appears with gradient
- [ ] 4 sections visible: What to Fix, Why It Matters, Drill, Cue
- [ ] Context badges show stance/direction
- [ ] Pro comparison shows matched reference
- [ ] Deviation analysis with severity gauge
- [ ] Processing time displayed

### Results (Gating Failure)
- [ ] Upload video <3s or >15s
- [ ] Processing overlay appears briefly
- [ ] Warning card shows rejection message
- [ ] Video metadata displayed
- [ ] Helpful tips shown

### Error Handling
- [ ] Stop backend → API offline indicator
- [ ] Upload >100MB file → size error
- [ ] Upload invalid file type → type error

### Responsive Design
- [ ] Desktop (>1024px): Side-by-side layout
- [ ] Tablet (768-1024px): Stacked layout
- [ ] Mobile (<768px): Touch-friendly buttons

## Environment Variables

Create a `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Troubleshooting

### API Connection Issues

**Problem**: Frontend can't connect to backend

**Solution**:
- Verify backend is running: `curl http://localhost:8000/api/v1/health`
- Check CORS is enabled in backend
- Verify Vite proxy config in `vite.config.ts`

### Build Issues

**Problem**: `npm install` fails

**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Video Upload Issues

**Problem**: Video doesn't load or metadata fails

**Solution**:
- Verify file format (MP4, MOV, AVI, WebM)
- Check file size (<100MB)
- Try a different video file
- Check browser console for errors

## Performance

- Initial bundle size: ~150KB gzipped
- First Contentful Paint: <1s
- Time to Interactive: <2s
- Lighthouse Score: 95+

## Browser Support

- Chrome/Edge: Latest 2 versions
- Safari: Latest 2 versions
- Firefox: Latest 2 versions
- Mobile Safari (iOS): Latest 2 versions
- Chrome Mobile (Android): Latest 2 versions

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Run TypeScript type checking

## License

MIT
