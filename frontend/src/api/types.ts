// TypeScript types matching backend schemas.py

export enum Stance {
  REGULAR = 'regular',
  GOOFY = 'goofy',
  UNKNOWN = 'unknown',
}

export enum Direction {
  FRONTSIDE = 'frontside',
  BACKSIDE = 'backside',
  UNKNOWN = 'unknown',
}

export enum RejectionReason {
  TOO_SHORT = 'too_short',
  TOO_LONG = 'too_long',
  LOW_RESOLUTION = 'low_resolution',
  LOW_FPS = 'low_fps',
  NO_PERSON = 'no_person',
  MULTIPLE_PEOPLE = 'multiple_people',
  HEAD_ON_ANGLE = 'head_on_angle',
  FROM_BEHIND_ANGLE = 'from_behind_angle',
  LOW_POSE_CONFIDENCE = 'low_pose_confidence',
}

export interface VideoMetadata {
  path: string;
  duration_seconds: number;
  width: number;
  height: number;
  fps: number;
  total_frames: number;
}

export interface GatingResult {
  passed: boolean;
  rejection_reason?: RejectionReason;
  rejection_message?: string;
  metadata?: VideoMetadata;
}

export interface ContextResult {
  stance: Stance;
  direction: Direction;
  wave_direction: string;
  confidence: number;
}

export interface ReferenceClip {
  clip_id: string;
  maneuver: string;
  stance: Stance;
  direction: Direction;
  style_tags: string[];
  surfer_name: string;
  source: string;
  camera_angle: string;
  quality_score: number;
  pose_file: string;
  embedding_file: string;
}

export interface MatchResult {
  matched_references: ReferenceClip[];
  style_cluster: string;
  similarity_scores: number[];
}

export interface JointDeviation {
  joint_name: string;
  mean_deviation: number;
  max_deviation: number;
  max_deviation_frame: number;
  max_deviation_phase: string;
}

export interface DeviationAnalysis {
  primary_error: string;
  primary_error_description: string;
  severity: number;
  phase: string;
  timing_offset_ms: number;
  joint_deviations: JointDeviation[];
}

export interface FeedbackResult {
  what_you_are_doing: string;
  what_to_fix: string;
  why_it_matters: string;
  dry_land_drill: string;
  in_water_cue: string;
  pro_insight: string;
  overlay_video_path?: string;
}

export interface AnalysisResult {
  video_path: string;
  gating: GatingResult;
  context?: ContextResult;
  pose_sequence?: any;
  match?: MatchResult;
  deviation?: DeviationAnalysis;
  feedback?: FeedbackResult;
  processing_time_ms: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}
