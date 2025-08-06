import React, { useEffect, useState } from 'react';
import { ChartView } from './ChartView';
import { useAnalysis } from '../hooks/useAnalysis';

interface ForecastPoint {
  date: string;
  actual: number | null;
  predicted: number;
  confidence_lower?: number;
  confidence_upper?: number;
}

interface ForecastChartProps {
  data?: ForecastPoint[];
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ data }) => {
  const { getForecast } = useAnalysis();
  const [forecastData, setForecastData] = useState<ForecastPoint[]>(data || []);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    if (data && data.length > 0) {
      setForecastData(data);
      setStartDate(data[0].date);
      setEndDate(data[data.length - 1].date);
    } else {
      getForecast().then(res => {
        if (res && Array.isArray(res.chart_data) && res.chart_data.length > 0) {
          setForecastData(res.chart_data as ForecastPoint[]);
          setStartDate(res.chart_data[0].date);
          setEndDate(res.chart_data[res.chart_data.length - 1].date);
        }
      });
    }
  }, [data, getForecast]);

  const filtered = forecastData.filter(p => {
    const afterStart = startDate ? p.date >= startDate : true;
    const beforeEnd = endDate ? p.date <= endDate : true;
    return afterStart && beforeEnd;
  });

  const chart = {
    type: 'line' as const,
    title: '销售预测',
    xAxis: { type: 'category', data: filtered.map(p => p.date) },
    series: [
      { name: '实际', data: filtered.map(p => p.actual), type: 'line' },
      { name: '预测', data: filtered.map(p => p.predicted), type: 'line' },
    ],
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        />
        <span className="text-sm">至</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        />
      </div>
      <ChartView data={chart} />
    </div>
  );
};

