export const PROCESSING_STAGES = [
  { number: 1, name: 'Quality Gating', description: 'Validating video quality...' },
  { number: 2, name: 'Pose Extraction', description: 'Extracting body pose...' },
  { number: 3, name: 'Context Detection', description: 'Detecting stance & direction...' },
  { number: 4, name: 'Reference Matching', description: 'Finding pro comparisons...' },
  { number: 5, name: 'DTW Alignment', description: 'Analyzing biomechanics...' },
  { number: 6, name: 'Feedback Generation', description: 'Generating coaching tips...' },
] as const;

export const ACCEPTED_VIDEO_TYPES = {
  'video/mp4': ['.mp4'],
  'video/quicktime': ['.mov'],
  'video/x-msvideo': ['.avi'],
  'video/webm': ['.webm'],
};

export const MAX_FILE_SIZE_MB = 100;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export const VALIDATION_CONSTRAINTS = {
  minDuration: 3,
  maxDuration: 15,
  minResolution: 480,
  minFps: 24,
  maxFileSize: MAX_FILE_SIZE_MB,
};

export const REJECTION_REASON_MESSAGES: Record<string, string> = {
  too_short: 'Video is too short. Must be at least 3 seconds.',
  too_long: 'Video is too long. Must be under 15 seconds.',
  low_resolution: 'Video resolution is too low. Minimum 480p required.',
  low_fps: 'Video framerate is too low. Minimum 24 FPS required.',
  no_person: 'No person detected in the video.',
  multiple_people: 'Multiple people detected. Only one surfer should be visible.',
  head_on_angle: 'Camera angle is head-on. Side view required.',
  from_behind_angle: 'Camera angle is from behind. Side view required.',
  low_pose_confidence: 'Body pose detection confidence too low.',
};
