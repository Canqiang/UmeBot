// ============== src/hooks/useAnalysis.ts ==============
import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { AnalysisResult, ForecastData } from '../types';

interface UseAnalysisReturn {
  runAnalysis: (startDate: string, endDate: string, type?: string) => Promise<AnalysisResult | null>;
  getForecast: (days?: number) => Promise<ForecastData | null>;
  isAnalyzing: boolean;
  error: Error | null;
}

export const useAnalysis = (): UseAnalysisReturn => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const runAnalysis = useCallback(async (
    startDate: string,
    endDate: string,
    type: string = 'full'
  ): Promise<AnalysisResult | null> => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await api.runAnalysis({
        start_date: startDate,
        end_date: endDate,
        analysis_type: type,
      });

      return result.data as AnalysisResult;
    } catch (err) {
      setError(err as Error);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const getForecast = useCallback(async (days: number = 7): Promise<ForecastData | null> => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await api.getForecast(days);
      return result.data as ForecastData;
    } catch (err) {
      setError(err as Error);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  return {
    runAnalysis,
    getForecast,
    isAnalyzing,
    error,
  };
};