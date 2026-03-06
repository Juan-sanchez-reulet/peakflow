import type { AnalysisResult } from '../api/types';
import { Stance, Direction } from '../api/types';

export const DEMO_RESULT: AnalysisResult = {
  video_path: 'demo/frontside_bottom_turn.mp4',
  gating: {
    passed: true,
    metadata: {
      path: 'demo/frontside_bottom_turn.mp4',
      duration_seconds: 8.2,
      width: 1920,
      height: 1080,
      fps: 30,
      total_frames: 246,
    },
  },
  context: {
    stance: Stance.REGULAR,
    direction: Direction.FRONTSIDE,
    wave_direction: 'left-to-right',
    confidence: 0.92,
  },
  pose_sequence: null,
  match: {
    matched_references: [
      {
        clip_id: 'demo-medina-bt-001',
        maneuver: 'bottom_turn',
        stance: Stance.REGULAR,
        direction: Direction.FRONTSIDE,
        style_tags: ['power', 'rail-to-rail', 'progressive'],
        surfer_name: 'Gabriel Medina',
        source: 'WSL Championship Tour 2024',
        camera_angle: 'water_side',
        quality_score: 0.95,
        pose_file: 'ref/medina_bt_001.npy',
        embedding_file: 'ref/medina_bt_001_emb.npy',
      },
      {
        clip_id: 'demo-jjf-bt-002',
        maneuver: 'bottom_turn',
        stance: Stance.REGULAR,
        direction: Direction.FRONTSIDE,
        style_tags: ['flow', 'smooth', 'stylish'],
        surfer_name: 'John John Florence',
        source: 'WSL Championship Tour 2024',
        camera_angle: 'water_side',
        quality_score: 0.93,
        pose_file: 'ref/jjf_bt_002.npy',
        embedding_file: 'ref/jjf_bt_002_emb.npy',
      },
      {
        clip_id: 'demo-italo-bt-003',
        maneuver: 'bottom_turn',
        stance: Stance.REGULAR,
        direction: Direction.FRONTSIDE,
        style_tags: ['explosive', 'aerial-setup', 'dynamic'],
        surfer_name: 'Italo Ferreira',
        source: 'WSL Championship Tour 2024',
        camera_angle: 'water_side',
        quality_score: 0.91,
        pose_file: 'ref/italo_bt_003.npy',
        embedding_file: 'ref/italo_bt_003_emb.npy',
      },
    ],
    style_cluster: 'power_carving',
    similarity_scores: [0.873, 0.821, 0.795],
  },
  deviation: {
    primary_error: 'knee_flexion_back',
    primary_error_description:
      'During the bottom turn initiation, your back knee lacks the deep compression seen in pro references. This limits the energy you can load into the turn and reduces drive off the bottom.',
    severity: 0.45,
    phase: 'bottom_turn_entry',
    timing_offset_ms: 120,
    joint_deviations: [
      {
        joint_name: 'knee_flexion_back',
        mean_deviation: 18.3,
        max_deviation: 24.7,
        max_deviation_frame: 87,
        max_deviation_phase: 'bottom_turn_entry',
      },
      {
        joint_name: 'hip_flexion',
        mean_deviation: 12.1,
        max_deviation: 16.8,
        max_deviation_frame: 92,
        max_deviation_phase: 'bottom_turn_entry',
      },
      {
        joint_name: 'torso_lean',
        mean_deviation: 9.4,
        max_deviation: 14.2,
        max_deviation_frame: 95,
        max_deviation_phase: 'mid_turn',
      },
      {
        joint_name: 'arm_elevation_leading',
        mean_deviation: 7.8,
        max_deviation: 11.5,
        max_deviation_frame: 98,
        max_deviation_phase: 'mid_turn',
      },
      {
        joint_name: 'knee_flexion_front',
        mean_deviation: 6.2,
        max_deviation: 9.3,
        max_deviation_frame: 90,
        max_deviation_phase: 'bottom_turn_entry',
      },
    ],
  },
  feedback: {
    what_you_are_doing:
      'Your back knee stays fairly straight as you enter the bottom turn — your stance is tall and extended instead of compressed and loaded. The upper body is also opening up a touch early before the board has finished the arc.',
    what_to_fix:
      'Focus on deepening your back knee compression as you initiate the bottom turn. Think about sitting into the turn like you\'re dropping into a low squat — really drive that back knee toward the deck.',
    why_it_matters:
      'The back knee acts as your primary spring mechanism during a bottom turn. Deeper compression stores more potential energy that gets released as speed and power through the turn.',
    dry_land_drill:
      'Practice deep single-leg squats (pistol squat progressions) with emphasis on the back leg. Hold the bottom position for 3 seconds, then explode up. Do 3 sets of 8 reps each leg. Add a resistance band around your knees to reinforce proper tracking.',
    in_water_cue:
      'Sit deep, spring hard',
    pro_insight:
      'Gabriel Medina drops his back knee almost to the deck before exploding upward through the turn. His whole body coils like a spring — hips low, chest stays quiet over the board — and he doesn\'t open up until the rail is fully engaged.',
  },
  processing_time_ms: 4820,
};
