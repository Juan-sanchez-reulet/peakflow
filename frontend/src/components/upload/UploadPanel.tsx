import { UploadZone } from './UploadZone';
import { VideoPreview } from './VideoPreview';
import { ValidationIndicators } from './ValidationIndicators';
import { AnalyzeButton } from './AnalyzeButton';
import { useUploadStore } from '../../store/useUploadStore';

export function UploadPanel() {
  const selectedFile = useUploadStore((state) => state.selectedFile);

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      {!selectedFile && <UploadZone />}

      {/* Video Preview */}
      {selectedFile && <VideoPreview />}

      {/* Validation Indicators */}
      {selectedFile && <ValidationIndicators />}

      {/* Analyze Button */}
      <AnalyzeButton />
    </div>
  );
}
