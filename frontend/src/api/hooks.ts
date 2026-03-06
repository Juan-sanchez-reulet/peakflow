import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { AnalysisResult, HealthResponse } from './types';

export function useApiHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>('/health');
      return data;
    },
    refetchInterval: 10000,
    retry: false,
    staleTime: 5000,
  });
}

export function useAnalyzeVideo() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('video', file);
      const { data } = await apiClient.post<AnalysisResult>('/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
  });
}
