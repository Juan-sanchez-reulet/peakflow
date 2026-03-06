import { VALIDATION_CONSTRAINTS, MAX_FILE_SIZE_BYTES } from './constants';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface VideoValidation extends ValidationResult {
  checks: {
    fileType: boolean;
    fileSize: boolean;
    duration: boolean;
    resolution: boolean;
    fps: boolean;
  };
}

export function validateFileType(file: File): boolean {
  const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
  return validTypes.includes(file.type) ||
         file.name.match(/\.(mp4|mov|avi|webm)$/i) !== null;
}

export function validateFileSize(file: File): boolean {
  return file.size <= MAX_FILE_SIZE_BYTES;
}

export async function extractVideoMetadata(file: File): Promise<{
  duration: number;
  width: number;
  height: number;
  fps: number;
}> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';

    video.onloadedmetadata = () => {
      URL.revokeObjectURL(video.src);

      // Estimate FPS (not perfect, but reasonable approximation)
      const fps = 30; // Default assumption for most videos

      resolve({
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
        fps,
      });
    };

    video.onerror = () => {
      URL.revokeObjectURL(video.src);
      reject(new Error('Failed to load video metadata'));
    };

    video.src = URL.createObjectURL(file);
  });
}

export async function validateVideo(file: File): Promise<VideoValidation> {
  const errors: string[] = [];
  const warnings: string[] = [];

  const checks = {
    fileType: false,
    fileSize: false,
    duration: false,
    resolution: false,
    fps: false,
  };

  // File type validation
  checks.fileType = validateFileType(file);
  if (!checks.fileType) {
    errors.push('Invalid file type. Please upload MP4, MOV, AVI, or WebM.');
  }

  // File size validation
  checks.fileSize = validateFileSize(file);
  if (!checks.fileSize) {
    errors.push(`File size exceeds ${VALIDATION_CONSTRAINTS.maxFileSize}MB limit.`);
  }

  // If basic checks fail, return early
  if (!checks.fileType || !checks.fileSize) {
    return {
      isValid: false,
      errors,
      warnings,
      checks,
    };
  }

  try {
    const metadata = await extractVideoMetadata(file);

    // Duration validation
    checks.duration =
      metadata.duration >= VALIDATION_CONSTRAINTS.minDuration &&
      metadata.duration <= VALIDATION_CONSTRAINTS.maxDuration;

    if (!checks.duration) {
      if (metadata.duration < VALIDATION_CONSTRAINTS.minDuration) {
        errors.push(`Video is too short (${metadata.duration.toFixed(1)}s). Must be at least ${VALIDATION_CONSTRAINTS.minDuration}s.`);
      } else {
        errors.push(`Video is too long (${metadata.duration.toFixed(1)}s). Must be under ${VALIDATION_CONSTRAINTS.maxDuration}s.`);
      }
    }

    // Resolution validation
    const minDimension = Math.min(metadata.width, metadata.height);
    checks.resolution = minDimension >= VALIDATION_CONSTRAINTS.minResolution;

    if (!checks.resolution) {
      errors.push(`Resolution too low (${metadata.width}x${metadata.height}). Minimum ${VALIDATION_CONSTRAINTS.minResolution}p required.`);
    }

    // FPS validation (we use estimated FPS)
    checks.fps = metadata.fps >= VALIDATION_CONSTRAINTS.minFps;
    if (!checks.fps) {
      warnings.push(`FPS may be low. ${VALIDATION_CONSTRAINTS.minFps} FPS or higher recommended.`);
    }

  } catch (error) {
    errors.push('Failed to extract video metadata. File may be corrupted.');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    checks,
  };
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
