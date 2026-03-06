import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUploadStore } from '../../store/useUploadStore';
import { PROCESSING_STAGES } from '../../utils/constants';
import { Spinner } from '../common/Spinner';
import clsx from 'clsx';

export function ProcessingOverlay() {
  const { isProcessing, currentStage } = useUploadStore();
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (isProcessing) {
      setElapsedSeconds(0);
      const interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isProcessing]);

  if (!isProcessing) return null;

  const currentStageInfo = PROCESSING_STAGES.find((s) => s.number === currentStage);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-surface border border-border rounded-2xl p-8 max-w-md w-full mx-4 space-y-6"
        >
          {/* Header */}
          <div className="text-center space-y-2">
            <Spinner size="lg" className="mx-auto text-accent" />
            <h2 className="text-xl font-bold text-text">Analyzing Your Surf</h2>
            <p className="text-sm text-text-dim">
              This usually takes 5-10 seconds
            </p>
          </div>

          {/* Stage Progress */}
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-text-dim">
                  Stage {currentStage} of {PROCESSING_STAGES.length}
                </span>
                <span className="text-text-dim">{elapsedSeconds}s</span>
              </div>
              <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-accent"
                  initial={{ width: 0 }}
                  animate={{ width: `${(currentStage / PROCESSING_STAGES.length) * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>

            {/* Current Stage */}
            {currentStageInfo && (
              <div className="p-4 bg-accent-glow border border-accent/30 rounded-lg">
                <p className="font-medium text-accent">{currentStageInfo.name}</p>
                <p className="text-sm text-text-dim mt-1">
                  {currentStageInfo.description}
                </p>
              </div>
            )}

            {/* Stage List */}
            <div className="space-y-2">
              {PROCESSING_STAGES.map((stage) => {
                const isComplete = stage.number < currentStage;
                const isCurrent = stage.number === currentStage;
                const isPending = stage.number > currentStage;

                return (
                  <div
                    key={stage.number}
                    className={clsx(
                      'flex items-center gap-3 text-sm transition-all',
                      {
                        'text-success': isComplete,
                        'text-accent': isCurrent,
                        'text-text-dim': isPending,
                      }
                    )}
                  >
                    {/* Icon */}
                    {isComplete ? (
                      <svg
                        className="w-5 h-5 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    ) : isCurrent ? (
                      <Spinner size="sm" className="flex-shrink-0" />
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-current flex-shrink-0" />
                    )}

                    {/* Label */}
                    <span>{stage.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
