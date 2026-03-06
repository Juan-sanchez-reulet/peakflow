import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { useUploadStore } from '../../store/useUploadStore';
import { validateVideo, VideoValidation } from '../../utils/validation';
import { Card } from '../common/Card';

export function ValidationIndicators() {
  const { selectedFile, videoMetadata } = useUploadStore();
  const [validation, setValidation] = useState<VideoValidation | null>(null);

  useEffect(() => {
    if (selectedFile) {
      validateVideo(selectedFile).then(setValidation);
    } else {
      setValidation(null);
    }
  }, [selectedFile, videoMetadata]);

  if (!selectedFile || !validation) return null;

  const checks = [
    { label: 'Valid file type', passed: validation.checks.fileType },
    { label: 'File size OK', passed: validation.checks.fileSize },
    { label: 'Duration 3-15s', passed: validation.checks.duration },
    { label: 'Resolution ≥480p', passed: validation.checks.resolution },
    { label: 'FPS ≥24', passed: validation.checks.fps },
  ];

  return (
    <Card padding="sm">
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-text-dim">Validation Checks</h3>

        <div className="space-y-1.5">
          {checks.map((check) => (
            <div key={check.label} className="flex items-center gap-2 text-sm">
              {check.passed ? (
                <svg
                  className="w-4 h-4 text-success flex-shrink-0"
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
              ) : (
                <svg
                  className="w-4 h-4 text-error flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
              <span
                className={clsx(
                  check.passed ? 'text-text' : 'text-error'
                )}
              >
                {check.label}
              </span>
            </div>
          ))}
        </div>

        {/* Errors */}
        {validation.errors.length > 0 && (
          <div className="mt-3 p-2 bg-error/10 border border-error/30 rounded text-xs text-error space-y-1">
            {validation.errors.map((error, i) => (
              <p key={i}>{error}</p>
            ))}
          </div>
        )}

        {/* Warnings */}
        {validation.warnings.length > 0 && (
          <div className="mt-3 p-2 bg-warning/10 border border-warning/30 rounded text-xs text-warning space-y-1">
            {validation.warnings.map((warning, i) => (
              <p key={i}>{warning}</p>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
