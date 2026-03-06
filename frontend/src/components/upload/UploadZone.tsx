import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import clsx from 'clsx';
import { useUploadStore } from '../../store/useUploadStore';
import { extractVideoMetadata } from '../../utils/validation';
import { ACCEPTED_VIDEO_TYPES, MAX_FILE_SIZE_BYTES } from '../../utils/constants';

export function UploadZone() {
  const { setFile, setVideoMetadata } = useUploadStore();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];

      // Set file immediately for preview
      setFile(file);

      try {
        // Extract metadata
        const metadata = await extractVideoMetadata(file);
        setVideoMetadata({
          duration: metadata.duration,
          width: metadata.width,
          height: metadata.height,
          fps: metadata.fps,
          size: file.size,
        });
      } catch (error) {
        console.error('Failed to extract video metadata:', error);
      }
    },
    [setFile, setVideoMetadata]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_VIDEO_TYPES,
    maxSize: MAX_FILE_SIZE_BYTES,
    multiple: false,
    disabled: false,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-xl p-12 transition-all duration-200 cursor-pointer',
        'hover:border-accent hover:bg-accent-glow',
        {
          'border-accent bg-accent-glow': isDragActive && !isDragReject,
          'border-error bg-error/10': isDragReject,
          'border-border': !isDragActive && !isDragReject,
        }
      )}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center justify-center text-center space-y-4">
        {/* Upload Icon */}
        <svg
          className={clsx(
            'w-16 h-16 transition-colors',
            isDragActive ? 'text-accent' : 'text-text-dim'
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        {/* Text */}
        <div>
          <p className="text-lg font-medium text-text">
            {isDragActive ? 'Drop your video here' : 'Drag & drop your surf video'}
          </p>
          <p className="text-sm text-text-dim mt-1">
            or click to browse
          </p>
        </div>

        {/* Requirements */}
        <div className="text-xs text-text-dim space-y-1">
          <p>MP4, MOV, AVI, or WebM • 3-15 seconds • Max 100MB</p>
          <p>Side angle • Single surfer visible</p>
        </div>
      </div>
    </div>
  );
}
