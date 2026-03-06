import { motion } from 'framer-motion';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';
import { formatStance, formatDirection } from '../../utils/formatters';
import type { ContextResult } from '../../api/types';

interface ContextBadgesProps {
  context: ContextResult;
}

export function ContextBadges({ context }: ContextBadgesProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
    >
      <Card className="space-y-3">
        <h3 className="text-sm font-medium text-text-dim">Detected Context</h3>

        <div className="flex flex-wrap gap-2">
          <Badge variant="info" size="md">
            {formatStance(context.stance)}
          </Badge>
          <Badge variant="info" size="md">
            {formatDirection(context.direction)}
          </Badge>
          <Badge variant="default" size="md">
            {context.wave_direction}
          </Badge>
        </div>
      </Card>
    </motion.div>
  );
}
