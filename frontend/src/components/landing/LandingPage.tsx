import { motion } from 'framer-motion';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { useUploadStore } from '../../store/useUploadStore';
import { useResultsStore } from '../../store/useResultsStore';
import { DEMO_RESULT } from '../../data/demoResult';
import { PROCESSING_STAGES } from '../../utils/constants';

const stageIcons: Record<number, string> = {
  1: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  2: 'M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5',
  3: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
  4: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  5: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
  6: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
};

const howItWorks = [
  {
    step: '01',
    title: 'Upload Your Video',
    description: 'Drop in a 3-15 second clip of your surfing from a side angle.',
    icon: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12',
  },
  {
    step: '02',
    title: 'AI Analyzes',
    description: '6-stage pipeline extracts your pose, matches pro references, and identifies deviations.',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
  {
    step: '03',
    title: 'Get Coaching',
    description: 'Receive personalized feedback with specific drills and in-water cues to improve.',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  },
];

export function LandingPage() {
  const { setView, setDemo } = useUploadStore();
  const { setResult } = useResultsStore();

  const handleUploadClick = () => {
    setView('upload');
  };

  const handleDemoClick = () => {
    setDemo(true);
    setResult(DEMO_RESULT);
    setView('results');
  };

  return (
    <div className="min-h-screen bg-bg">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-16">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center gap-3 mb-16"
          >
            <img src="/wave-icon.svg" alt="PeakFlow" className="h-10 w-10" />
            <h1 className="text-3xl font-bold bg-gradient-accent bg-clip-text text-transparent">
              PeakFlow
            </h1>
          </motion.div>

          {/* Hero content */}
          <div className="max-w-3xl">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl sm:text-6xl font-bold text-text leading-tight"
            >
              AI-Powered{' '}
              <span className="bg-gradient-accent bg-clip-text text-transparent">
                Surf Coaching
              </span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl text-text-dim mt-6 max-w-2xl leading-relaxed"
            >
              Upload a clip of your surfing and get instant biomechanical analysis
              compared to world-class professionals. Personalized coaching feedback
              in under 5 seconds.
            </motion.p>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-wrap gap-4 mt-10"
            >
              <Button
                size="lg"
                onClick={handleUploadClick}
                className="animate-pulse-glow"
              >
                Upload Your Video
              </Button>
              <Button
                variant="secondary"
                size="lg"
                onClick={handleDemoClick}
              >
                See Demo
              </Button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Pipeline Visualization */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <h3 className="text-sm font-semibold text-accent uppercase tracking-wider mb-8">
            6-Stage AI Pipeline
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {PROCESSING_STAGES.map((stage, index) => (
              <motion.div
                key={stage.number}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.5 + index * 0.1 }}
              >
                <Card className="h-full text-center space-y-3 relative group hover:border-accent/50 transition-colors">
                  {/* Connector line (hidden on first item and mobile) */}
                  {index > 0 && (
                    <div className="absolute -left-4 top-1/2 w-4 h-px bg-border hidden lg:block group-hover:bg-accent/50 transition-colors" />
                  )}

                  <div className="mx-auto w-10 h-10 rounded-lg bg-accent-glow flex items-center justify-center">
                    <svg
                      className="w-5 h-5 text-accent"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d={stageIcons[stage.number]}
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs text-accent font-medium">
                      Stage {stage.number}
                    </p>
                    <p className="text-sm font-semibold text-text mt-0.5">
                      {stage.name}
                    </p>
                    <p className="text-xs text-text-dim mt-1">
                      {stage.description.replace('...', '')}
                    </p>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Stats Bar */}
      <section className="border-y border-border bg-surface/30">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center"
          >
            {[
              { value: '43', label: 'Pro References' },
              { value: '7', label: 'World-Class Surfers' },
              { value: '6', label: 'Stage AI Pipeline' },
              { value: '<5s', label: 'Analysis Time' },
            ].map((stat) => (
              <div key={stat.label}>
                <p className="text-2xl sm:text-3xl font-bold bg-gradient-accent bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-sm text-text-dim mt-1">{stat.label}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.9 }}
        >
          <h3 className="text-sm font-semibold text-accent uppercase tracking-wider mb-8">
            How It Works
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {howItWorks.map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 1.0 + index * 0.15 }}
              >
                <Card padding="lg" className="h-full space-y-4 hover:border-accent/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl font-bold text-accent/30">
                      {item.step}
                    </span>
                    <div className="w-10 h-10 rounded-lg bg-accent-glow flex items-center justify-center">
                      <svg
                        className="w-5 h-5 text-accent"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d={item.icon}
                        />
                      </svg>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-text">{item.title}</h4>
                  <p className="text-sm text-text-dim leading-relaxed">
                    {item.description}
                  </p>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Footer CTA */}
      <section className="max-w-7xl mx-auto px-6 pb-20 text-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="space-y-4"
        >
          <p className="text-text-dim">
            Ready to level up your surfing?
          </p>
          <Button size="lg" onClick={handleUploadClick} className="animate-pulse-glow">
            Get Started
          </Button>
        </motion.div>
      </section>
    </div>
  );
}
