import { motion } from 'framer-motion';
import { Card } from '../common/Card';
import { REJECTION_REASON_MESSAGES } from '../../utils/constants';
import { formatDuration } from '../../utils/validation';
import type { GatingResult } from '../../api/types';

interface ErrorMessageProps {
  gating: GatingResult;
}

export function ErrorMessage({ gating }: ErrorMessageProps) {
  const reasonMessage =
    gating.rejection_reason && REJECTION_REASON_MESSAGES[gating.rejection_reason]
      ? REJECTION_REASON_MESSAGES[gating.rejection_reason]
      : gating.rejection_message || 'Video did not pass quality checks.';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className="space-y-4 border-warning/30 bg-warning/5">
        {/* Header */}
        <div className="flex items-start gap-3">
          <svg
            className="w-6 h-6 text-warning flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div className="flex-1">
            <h3 className="font-semibold text-warning">Video Quality Issue</h3>
            <p className="text-sm text-text-dim mt-1">{reasonMessage}</p>
          </div>
        </div>

        {/* Video Metadata */}
        {gating.metadata && (
          <div className="p-3 bg-surface rounded-lg space-y-2">
            <p className="text-xs font-medium text-text-dim">Video Details:</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-text-dim">Duration:</span>{' '}
                <span className="text-text">
                  {formatDuration(gating.metadata.duration_seconds)}
                </span>
              </div>
              <div>
                <span className="text-text-dim">Resolution:</span>{' '}
                <span className="text-text">
                  {gating.metadata.width}x{gating.metadata.height}
                </span>
              </div>
              <div>
                <span className="text-text-dim">FPS:</span>{' '}
                <span className="text-text">{gating.metadata.fps}</span>
              </div>
              <div>
                <span className="text-text-dim">Frames:</span>{' '}
                <span className="text-text">{gating.metadata.total_frames}</span>
              </div>
            </div>
          </div>
        )}

        {/* Suggestions */}
        <div className="text-xs text-text-dim space-y-1">
          <p className="font-medium text-text">Tips for a better video:</p>
          <ul className="list-disc list-inside space-y-0.5 ml-2">
            <li>Film from a side angle (not head-on or from behind)</li>
            <li>Keep duration between 3-15 seconds</li>
            <li>Ensure only one surfer is visible</li>
            <li>Use at least 480p resolution and 24 FPS</li>
          </ul>
        </div>
      </Card>
    </motion.div>
  );
}
