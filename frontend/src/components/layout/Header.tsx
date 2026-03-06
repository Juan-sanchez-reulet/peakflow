import { useApiHealth } from '../../api/hooks';
import { useUploadStore } from '../../store/useUploadStore';
import { useResultsStore } from '../../store/useResultsStore';
import clsx from 'clsx';

export function Header() {
  const { data: health, isError } = useApiHealth();
  const { view, reset, setView } = useUploadStore();
  const { clearResults } = useResultsStore();

  const isOnline = health?.status === 'healthy';

  const handleLogoClick = () => {
    clearResults();
    reset();
  };

  const handleUploadClick = () => {
    setView('upload');
  };

  return (
    <header className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={handleLogoClick}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <img src="/wave-icon.svg" alt="PeakFlow" className="h-8 w-8" />
          <h1 className="text-2xl font-bold bg-gradient-accent bg-clip-text text-transparent">
            PeakFlow
          </h1>
          <span className="text-text-dim text-sm hidden sm:inline">
            AI Surf Coaching
          </span>
        </button>

        {/* Nav + Status */}
        <div className="flex items-center gap-4">
          {/* Upload nav link (visible when not on upload) */}
          {view !== 'upload' && view !== 'processing' && (
            <button
              onClick={handleUploadClick}
              className="text-sm text-text-dim hover:text-accent transition-colors"
            >
              Upload
            </button>
          )}

          {/* API Status Indicator */}
          <div className="flex items-center gap-2">
            <div
              className={clsx(
                'h-2 w-2 rounded-full transition-colors',
                isOnline ? 'bg-success animate-pulse' : 'bg-error'
              )}
            />
            <span className="text-sm text-text-dim">
              {isError ? 'API Offline' : isOnline ? 'Connected' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
