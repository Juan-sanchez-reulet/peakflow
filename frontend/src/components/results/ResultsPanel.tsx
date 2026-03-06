import { useResultsStore } from '../../store/useResultsStore';
import { CoachingFeedback } from './CoachingFeedback';
import { ContextBadges } from './ContextBadges';
import { ProComparison } from './ProComparison';
import { ErrorMessage } from './ErrorMessage';
import { formatProcessingTime } from '../../utils/formatters';

export function ResultsPanel() {
  const currentResult = useResultsStore((state) => state.currentResult);

  if (!currentResult) {
    return (
      <aside className="space-y-6">
        <div className="p-8 text-center text-text-dim">
          <svg
            className="w-16 h-16 mx-auto mb-4 opacity-50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p className="text-sm">Results will appear here after analysis</p>
        </div>
      </aside>
    );
  }

  const { gating, context, match, feedback, processing_time_ms } =
    currentResult;

  // Gating failed - show error
  if (!gating.passed) {
    return (
      <aside className="space-y-6">
        <ErrorMessage gating={gating} />
      </aside>
    );
  }

  // Successful analysis - show results
  return (
    <aside className="space-y-6">
      {/* Processing Time */}
      <div className="text-xs text-text-dim text-center">
        Analysis completed in {formatProcessingTime(processing_time_ms)}
      </div>

      {/* Coaching Feedback (Hero Card) */}
      {feedback && <CoachingFeedback feedback={feedback} />}

      {/* Context Badges */}
      {context && <ContextBadges context={context} />}

      {/* Pro Comparison */}
      {match && <ProComparison match={match} />}

    </aside>
  );
}
