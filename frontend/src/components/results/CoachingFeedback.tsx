import { motion } from 'framer-motion';
import { Card } from '../common/Card';
import type { FeedbackResult } from '../../api/types';

interface CoachingFeedbackProps {
  feedback: FeedbackResult;
}

export function CoachingFeedback({ feedback }: CoachingFeedbackProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card variant="gradient" padding="lg" className="space-y-6 text-white">
        <h2 className="text-2xl font-bold">Coaching Feedback</h2>

        {/* What We See */}
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider opacity-90">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            What We See
          </h3>
          <p className="text-base leading-relaxed opacity-85">{feedback.what_you_are_doing}</p>
        </div>

        {/* What to Fix */}
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider opacity-90">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            What to Fix
          </h3>
          <p className="text-base leading-relaxed">{feedback.what_to_fix}</p>
        </div>

        {/* Why It Matters */}
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider opacity-90">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Why It Matters
          </h3>
          <p className="text-base leading-relaxed">{feedback.why_it_matters}</p>
        </div>

        {/* Pro Insight */}
        <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg p-4 space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider opacity-90">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            Pro Insight
          </h3>
          <p className="text-base leading-relaxed">{feedback.pro_insight}</p>
        </div>

        {/* Dry Land Drill */}
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider opacity-90">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            Dry Land Drill
          </h3>
          <p className="text-base leading-relaxed">{feedback.dry_land_drill}</p>
        </div>

        {/* In-Water Cue - Highlighted */}
        <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg p-6">
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider opacity-90 mb-3">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            In-Water Cue
          </h3>
          <p className="text-xl font-bold tracking-wide">
            {feedback.in_water_cue}
          </p>
        </div>
      </Card>
    </motion.div>
  );
}
