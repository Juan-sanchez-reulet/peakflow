import { useEffect, useRef } from 'react';
import { useUploadStore } from '../../store/useUploadStore';
import { formatFileSize, formatDuration } from '../../utils/validation';
import { Card } from '../common/Card';

export function VideoPreview() {
  const { selectedFile, videoMetadata } = useUploadStore();
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (selectedFile && videoRef.current) {
      const url = URL.createObjectURL(selectedFile);
      videoRef.current.src = url;

      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [selectedFile]);

  if (!selectedFile) return null;

  return (
    <Card className="space-y-4">
      {/* Video Player */}
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
        <video
          ref={videoRef}
          controls
          className="w-full h-full object-contain"
          preload="metadata"
        />
      </div>

      {/* Metadata */}
      {videoMetadata && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div>
            <p className="text-text-dim">Duration</p>
            <p className="text-text font-medium">
              {formatDuration(videoMetadata.duration)}
            </p>
          </div>
          <div>
            <p className="text-text-dim">Resolution</p>
            <p className="text-text font-medium">
              {videoMetadata.width}x{videoMetadata.height}
            </p>
          </div>
          <div>
            <p className="text-text-dim">FPS</p>
            <p className="text-text font-medium">{videoMetadata.fps}</p>
          </div>
          <div>
            <p className="text-text-dim">Size</p>
            <p className="text-text font-medium">
              {formatFileSize(videoMetadata.size)}
            </p>
          </div>
        </div>
      )}

      {/* Filename */}
      <div className="flex items-center gap-2 text-sm">
        <svg
          className="w-4 h-4 text-accent"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
        <span className="text-text-dim truncate">{selectedFile.name}</span>
      </div>
    </Card>
  );
}
