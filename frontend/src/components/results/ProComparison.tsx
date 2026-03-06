import { motion } from 'framer-motion';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { formatStance, formatDirection } from '../../utils/formatters';
import type { MatchResult } from '../../api/types';

interface ProComparisonProps {
  match: MatchResult;
}

export function ProComparison({ match }: ProComparisonProps) {
  const topMatch = match.matched_references[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
    >
      <Card className="space-y-4">
        <h3 className="text-sm font-medium text-text-dim">Pro Comparison</h3>

        {/* Top Match */}
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-lg font-bold text-text">{topMatch.surfer_name}</p>
              <p className="text-sm text-text-dim capitalize">{topMatch.maneuver}</p>
            </div>
            <Badge variant="success" size="md">
              Closest Match
            </Badge>
          </div>

          {/* Details */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="default" size="sm">
              {formatStance(topMatch.stance)}
            </Badge>
            <Badge variant="default" size="sm">
              {formatDirection(topMatch.direction)}
            </Badge>
            <Badge variant="default" size="sm">
              {topMatch.camera_angle}
            </Badge>
          </div>

          {/* Style Tags */}
          {topMatch.style_tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {topMatch.style_tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-0.5 bg-accent-glow text-accent rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Source */}
          <p className="text-xs text-text-dim">Source: {topMatch.source}</p>
        </div>

        {/* Additional Matches */}
        {match.matched_references.length > 1 && (
          <div className="pt-3 border-t border-border space-y-2">
            <p className="text-xs font-medium text-text-dim">Other Similar Pros:</p>
            {match.matched_references.slice(1, 3).map((ref) => (
              <div key={ref.clip_id} className="flex items-center justify-between text-sm">
                <span className="text-text">{ref.surfer_name}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </motion.div>
  );
}
