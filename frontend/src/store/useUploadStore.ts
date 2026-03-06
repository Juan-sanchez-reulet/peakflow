import { create } from 'zustand';

export type AppView = 'landing' | 'upload' | 'processing' | 'results';

interface UploadState {
  view: AppView;
  isDemo: boolean;
  selectedFile: File | null;
  isProcessing: boolean;
  currentStage: number;
  videoMetadata: {
    duration: number;
    width: number;
    height: number;
    fps: number;
    size: number;
  } | null;
  setView: (view: AppView) => void;
  setDemo: (isDemo: boolean) => void;
  setFile: (file: File | null) => void;
  setVideoMetadata: (metadata: UploadState['videoMetadata']) => void;
  startProcessing: () => void;
  updateStage: (stage: number) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  view: 'landing',
  isDemo: false,
  selectedFile: null,
  isProcessing: false,
  currentStage: 0,
  videoMetadata: null,
  setView: (view) => set({ view }),
  setDemo: (isDemo) => set({ isDemo }),
  setFile: (file) => set({ selectedFile: file }),
  setVideoMetadata: (metadata) => set({ videoMetadata: metadata }),
  startProcessing: () => set({ isProcessing: true, currentStage: 1, view: 'processing' }),
  updateStage: (stage) => set({ currentStage: stage }),
  reset: () => set({
    view: 'landing',
    isDemo: false,
    selectedFile: null,
    isProcessing: false,
    currentStage: 0,
    videoMetadata: null,
  }),
}));
