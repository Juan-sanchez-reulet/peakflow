import { motion } from 'framer-motion';
import { Button } from '../common/Button';
import { CoachingFeedback } from './CoachingFeedback';
import { ContextBadges } from './ContextBadges';
import { ProComparison } from './ProComparison';
import { ErrorMessage } from './ErrorMessage';
import { useUploadStore } from '../../store/useUploadStore';
import { useResultsStore } from '../../store/useResultsStore';
import { formatProcessingTime } from '../../utils/formatters';

export function ResultsView() {
  const { isDemo, setView, setDemo, reset } = useUploadStore();
  const { currentResult, clearResults } = useResultsStore();

  const handleAnalyzeAnother = () => {
    clearResults();
    setDemo(false);
    setView('upload');
  };

  const handleBackToLanding = () => {
    clearResults();
    reset();
  };

  if (!currentResult) return null;

  const { gating, context, match, feedback, processing_time_ms } =
    currentResult;

  // Gating failed
  if (!gating.passed) {
    return (
      <main className="max-w-7xl mx-auto p-6">
        <ErrorMessage gating={gating} />
        <div className="mt-6 text-center">
          <Button onClick={handleAnalyzeAnother}>Try Another Video</Button>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Demo Banner */}
      {isDemo && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-accent-glow border border-accent/30 rounded-lg px-4 py-2.5 flex items-center justify-between"
        >
          <div className="flex items-center gap-2 text-sm text-accent">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Demo Mode - Upload your own video for real analysis</span>
          </div>
          <Button variant="ghost" size="sm" onClick={handleAnalyzeAnother}>
            Upload Video
          </Button>
        </motion.div>
      )}

      {/* Top Bar */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-success animate-pulse" />
          <h2 className="text-xl font-bold text-text">Analysis Complete</h2>
          <span className="text-sm text-text-dim">
            {formatProcessingTime(processing_time_ms)}
          </span>
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" size="sm" onClick={handleBackToLanding}>
            Home
          </Button>
          <Button variant="secondary" size="sm" onClick={handleAnalyzeAnother}>
            Analyze Another
          </Button>
        </div>
      </motion.div>

      {/* Coaching Feedback - Full Width Hero */}
      {feedback && <CoachingFeedback feedback={feedback} />}

      {/* Bottom Row - Context + Pro Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {context && <ContextBadges context={context} />}
        {match && <ProComparison match={match} />}
      </div>
    </main>
  );
}
