import { create } from 'zustand';
import type { AnalysisResult } from '../api/types';

interface ResultsState {
  currentResult: AnalysisResult | null;
  setResult: (result: AnalysisResult) => void;
  clearResults: () => void;
}

export const useResultsStore = create<ResultsState>((set) => ({
  currentResult: null,
  setResult: (result) => set({ currentResult: result }),
  clearResults: () => set({ currentResult: null }),
}));
