import { UploadPanel } from '../upload/UploadPanel';
import { ResultsPanel } from '../results/ResultsPanel';
import { ProcessingOverlay } from '../processing/ProcessingOverlay';
import { useUploadStore } from '../../store/useUploadStore';

export function AppLayout() {
  const isProcessing = useUploadStore((state) => state.isProcessing);

  return (
    <main className="max-w-7xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_420px] gap-6">
        {/* Main Upload Panel */}
        <UploadPanel />

        {/* Results Sidebar */}
        <ResultsPanel />
      </div>

      {/* Processing Overlay Modal */}
      {isProcessing && <ProcessingOverlay />}
    </main>
  );
}
