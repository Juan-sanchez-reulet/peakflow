import { useEffect, useState } from 'react';
import { Button } from '../common/Button';
import { useUploadStore } from '../../store/useUploadStore';
import { useResultsStore } from '../../store/useResultsStore';
import { useAnalyzeVideo } from '../../api/hooks';
import { validateVideo } from '../../utils/validation';

export function AnalyzeButton() {
  const { selectedFile, startProcessing, updateStage, setView } = useUploadStore();
  const { setResult, clearResults } = useResultsStore();
  const [isValid, setIsValid] = useState(false);

  const analyzeMutation = useAnalyzeVideo();

  useEffect(() => {
    if (selectedFile) {
      validateVideo(selectedFile).then((validation) => {
        setIsValid(validation.isValid);
      });
    } else {
      setIsValid(false);
    }
  }, [selectedFile]);

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    startProcessing();

    // Simulate stage progression
    let currentStageNum = 1;
    const stageInterval = setInterval(() => {
      if (currentStageNum < 6) {
        currentStageNum++;
        updateStage(currentStageNum);
      }
    }, 1500);

    try {
      const result = await analyzeMutation.mutateAsync(selectedFile);
      clearInterval(stageInterval);
      setResult(result);
      useUploadStore.setState({ isProcessing: false, currentStage: 0 });
      setView('results');
    } catch (error) {
      clearInterval(stageInterval);
      useUploadStore.setState({ isProcessing: false, currentStage: 0 });
      setView('upload');
      console.error('Analysis failed:', error);
    }
  };

  const handleReset = () => {
    useUploadStore.setState({
      selectedFile: null,
      isProcessing: false,
      currentStage: 0,
      videoMetadata: null,
    });
    clearResults();
  };

  if (!selectedFile) return null;

  return (
    <div className="flex gap-3">
      <Button
        size="lg"
        onClick={handleAnalyze}
        disabled={!isValid || analyzeMutation.isPending}
        loading={analyzeMutation.isPending}
        className="flex-1"
      >
        {analyzeMutation.isPending ? 'Analyzing...' : 'Analyze My Surf'}
      </Button>

      <Button variant="secondary" onClick={handleReset}>
        Clear
      </Button>
    </div>
  );
}
