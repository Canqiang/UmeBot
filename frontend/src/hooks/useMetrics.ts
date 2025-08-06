// ============== src/hooks/useMetrics.ts ==============
import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import { Metrics, DailyReport } from '../types';

interface UseMetricsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseMetricsReturn {
  metrics: Metrics | null;
  dailyReport: DailyReport | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export const useMetrics = ({
  autoRefresh = false,
  refreshInterval = 60000, // 1 minute
}: UseMetricsOptions = {}): UseMetricsReturn => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const reportResult = await api.getDailyReport();

      if (reportResult.data) {
        setDailyReport(reportResult.data as DailyReport);

        // Extract metrics from daily report including item count and new users
        if (reportResult.data.metrics) {
          setMetrics(reportResult.data.metrics as Metrics);
        }
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchData]);

  return {
    metrics,
    dailyReport,
    isLoading,
    error,
    refresh: fetchData,
  };
};