import { Stance, Direction } from '../api/types';

export function formatStance(stance: Stance): string {
  return stance.charAt(0).toUpperCase() + stance.slice(1);
}

export function formatDirection(direction: Direction): string {
  return direction.charAt(0).toUpperCase() + direction.slice(1);
}

export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatSeverity(severity: number): {
  label: string;
  color: string;
} {
  if (severity < 0.3) {
    return { label: 'Minor', color: 'text-success' };
  } else if (severity < 0.7) {
    return { label: 'Moderate', color: 'text-warning' };
  } else {
    return { label: 'Significant', color: 'text-error' };
  }
}

export function formatJointName(jointName: string): string {
  return jointName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatProcessingTime(ms: number): string {
  const seconds = ms / 1000;
  if (seconds < 1) return `${ms}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
}
