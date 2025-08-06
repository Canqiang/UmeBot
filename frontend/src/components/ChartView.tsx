import React, { useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import * as echarts from 'echarts';

interface ChartViewProps {
  data: {
    type: 'line' | 'bar' | 'pie' | 'scatter' | 'mixed';
    title?: string;
    series: any[];
    xAxis?: any;
    yAxis?: any;
    options?: any;
  };
  onPointClick?: (params: any) => void;
}

export const ChartView: React.FC<ChartViewProps> = ({ data, onPointClick }) => {
  const chartRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chartRef.current) {
      const chart = echarts.init(chartRef.current);

      const option = buildChartOption(data);
      chart.setOption(option);

      const handleResize = () => chart.resize();
      const handleClick = (params: any) => {
        if (onPointClick) {
          onPointClick(params);
        }
      };

      window.addEventListener('resize', handleResize);
      chart.on('click', handleClick);

      return () => {
        window.removeEventListener('resize', handleResize);
        chart.off('click', handleClick);
        chart.dispose();
      };
    }
  }, [data, onPointClick]);

  const buildChartOption = (data: ChartViewProps['data']) => {
    const baseOption = {
      title: {
        text: data.title || '',
        left: 'center',
        top: 0
      },
      tooltip: {
        trigger: data.type === 'pie' ? 'item' : 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: {
          color: '#374151'
        }
      },
      legend: {
        bottom: 0,
        data: data.series.map(s => s.name)
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      }
    };

    if (data.type === 'pie') {
      return {
        ...baseOption,
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          data: data.series,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            formatter: '{b}: {c} ({d}%)'
          }
        }]
      };
    }

    return {
      ...baseOption,
      xAxis: data.xAxis || { type: 'category', data: [] },
      yAxis: data.yAxis || { type: 'value' },
      series: data.series.map(s => ({
        ...s,
        type: s.type || data.type || 'line',
        smooth: s.smooth !== false,
        areaStyle: s.areaStyle || (data.type === 'line' ? { opacity: 0.1 } : undefined)
      })),
      ...data.options
    };
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-gray-500" />
          <span className="font-medium">数据可视化</span>
        </div>
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '500px' }} />
    </div>
  );
};