// frontend/src/components/ForecastChart.tsx
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Calendar, TrendingUp, Info } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface ForecastPoint {
  date: string;
  actual: number | null;
  predicted: number;
  confidence_lower?: number;
  confidence_upper?: number;
}

interface ForecastChartProps {
  data?: ForecastPoint[] | any;
  onPointClick?: (params: any) => void;
  onRender?: () => void;
  height?: string;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ data, onPointClick, onRender, height = '500px' }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartInstance, setChartInstance] = useState<echarts.ECharts | null>(null);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [showConfidence, setShowConfidence] = useState(true);
  const [hoveredPoint, setHoveredPoint] = useState<ForecastPoint | null>(null);

  useEffect(() => {
    if (chartRef.current) {
      const chart = echarts.init(chartRef.current, 'light', {
        renderer: 'canvas'
      });
      setChartInstance(chart);

      const handleResize = () => chart.resize();
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        chart.dispose();
      };
    }
  }, []);

  useEffect(() => {
    if (chartInstance && data) {
      updateChart();
    }
  }, [chartInstance, data, showConfidence, dateRange, onRender]);

  useEffect(() => {
    if (chartInstance) {
      chartInstance.resize();
    }
  }, [chartInstance, height]);

  const updateChart = () => {
    if (!chartInstance || !data) return;

    let forecastData: ForecastPoint[] = [];

    // 处理不同格式的数据
    if (Array.isArray(data)) {
      if (data.length > 0 && data[0].date) {
        forecastData = data;
      }
    } else if (data.chart_data && Array.isArray(data.chart_data)) {
      forecastData = data.chart_data;
    }

    if (forecastData.length === 0) return;

    // 过滤日期范围
    let filteredData = forecastData;
    if (dateRange.start || dateRange.end) {
      filteredData = forecastData.filter(point => {
        const pointDate = new Date(point.date);
        const startDate = dateRange.start ? new Date(dateRange.start) : new Date('1900-01-01');
        const endDate = dateRange.end ? new Date(dateRange.end) : new Date('2100-01-01');
        return pointDate >= startDate && pointDate <= endDate;
      });
    }

    // 分离历史数据和预测数据
    const historicalData = filteredData.filter(p => p.actual !== null && p.actual !== undefined);
    const futureData = filteredData.filter(p => p.actual === null || p.actual === undefined);

    // 准备图表数据
    const dates = filteredData.map(p => p.date);
    const actualValues = filteredData.map(p => p.actual);
    const predictedValues = filteredData.map(p => p.predicted);
    const lowerBounds = filteredData.map(p => p.confidence_lower || p.predicted);
    const upperBounds = filteredData.map(p => p.confidence_upper || p.predicted);

    // 配置图表选项
    const option: echarts.EChartsOption = {
      title: {
        text: '销售额预测趋势',
        subtext: `历史数据: ${historicalData.length}天 | 预测数据: ${futureData.length}天`,
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        },
        subtextStyle: {
          fontSize: 12,
          color: '#666'
        }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: 12,
        textStyle: {
          color: '#374151',
          fontSize: 12
        },
        formatter: (params: any) => {
          const date = params[0].axisValue;
          const formattedDate = format(new Date(date), 'yyyy年MM月dd日 EEEE', { locale: zhCN });
          
          let html = `<div style="font-weight: bold; margin-bottom: 8px;">${formattedDate}</div>`;
          
          params.forEach((param: any) => {
            if (param.value !== null && param.value !== undefined) {
              const color = param.color;
              const value = typeof param.value === 'number' ? param.value.toFixed(2) : param.value;
              
              html += `
                <div style="display: flex; align-items: center; margin: 4px 0;">
                  <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${color}; margin-right: 8px;"></span>
                  <span style="flex: 1;">${param.seriesName}:</span>
                  <span style="font-weight: bold;">$${Number(value).toLocaleString()}</span>
                </div>
              `;
            }
          });

          // 添加置信区间信息
          const index = dates.indexOf(date);
          if (index >= 0 && lowerBounds[index] && upperBounds[index]) {
            html += `
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 11px;">
                置信区间: $${Number(lowerBounds[index]).toLocaleString()} - $${Number(upperBounds[index]).toLocaleString()}
              </div>
            `;
          }

          return html;
        }
      },
      legend: {
        data: ['实际销售额', '预测销售额', '置信区间'],
        bottom: 10,
        left: 'center',
        itemGap: 20,
        textStyle: {
          fontSize: 12
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '20%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: {
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          rotate: 45,
          formatter: (value: string) => {
            return format(new Date(value), 'MM/dd', { locale: zhCN });
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      yAxis: {
        type: 'value',
        name: '销售额 ($)',
        nameLocation: 'middle',
        nameGap: 50,
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          formatter: (value: number) => `$${(value / 1000).toFixed(0)}k`
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
          filterMode: 'none'
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          bottom: 40,
          height: 20,
          handleSize: '100%',
          handleStyle: {
            color: '#3b82f6'
          },
          dataBackground: {
            lineStyle: {
              color: '#e5e7eb'
            },
            areaStyle: {
              color: '#f3f4f6'
            }
          },
          borderColor: '#e5e7eb'
        }
      ],
      series: [
        // 置信区间（显示为区域）
        showConfidence ? {
          name: '置信区间',
          type: 'line',
          data: upperBounds,
          lineStyle: {
            opacity: 0
          },
          stack: 'confidence',
          symbol: 'none',
          areaStyle: {
            color: 'rgba(147, 197, 253, 0.2)'
          },
          silent: true
        } : null,
        showConfidence ? {
          name: '置信区间下界',
          type: 'line',
          data: lowerBounds,
          lineStyle: {
            opacity: 0
          },
          stack: 'confidence',
          symbol: 'none',
          areaStyle: {
            color: 'rgba(255, 255, 255, 1)'
          },
          silent: true,
          showInLegend: false
        } : null,
        // 实际销售额
        {
          name: '实际销售额',
          type: 'line',
          data: actualValues,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: {
            color: '#3b82f6',
            borderWidth: 2,
            borderColor: '#fff'
          },
          lineStyle: {
            color: '#3b82f6',
            width: 3,
            shadowColor: 'rgba(59, 130, 246, 0.3)',
            shadowBlur: 10
          },
          emphasis: {
            scale: 1.5,
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(59, 130, 246, 0.5)'
            }
          }
        },
        // 预测销售额
        {
          name: '预测销售额',
          type: 'line',
          data: predictedValues,
          smooth: true,
          symbol: 'diamond',
          symbolSize: 6,
          itemStyle: {
            color: '#10b981',
            borderWidth: 2,
            borderColor: '#fff'
          },
          lineStyle: {
            color: '#10b981',
            width: 2,
            type: 'dashed'
          },
          emphasis: {
            scale: 1.5,
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(16, 185, 129, 0.5)'
            }
          }
        }
      ].filter(Boolean) as echarts.SeriesOption[]
    };

    chartInstance.setOption(option);

    // 触发渲染完成回调
    chartInstance.off('finished');
    chartInstance.on('finished', () => {
      if (onRender) {
        onRender();
      }
    });

    // 添加点击事件
    chartInstance.off('click');
    chartInstance.on('click', (params: any) => {
      if (onPointClick) {
        onPointClick(params);
      }

      // 更新悬停的数据点
      const index = dates.indexOf(params.name);
      if (index >= 0) {
        setHoveredPoint(filteredData[index]);
      }
    });
  };

  // 设置日期范围为最近30天
  const setRecentDays = (days: number) => {
    if (!data) return;
    
    const forecastData = Array.isArray(data) ? data : data.chart_data || [];
    if (forecastData.length === 0) return;

    const lastDate = new Date(forecastData[forecastData.length - 1].date);
    const startDate = new Date(lastDate);
    startDate.setDate(startDate.getDate() - days);

    setDateRange({
      start: startDate.toISOString().split('T')[0],
      end: lastDate.toISOString().split('T')[0]
    });
  };

  return (
    <div className="space-y-4">
      {/* 控制面板 */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">时间范围</span>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-500">至</span>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setRecentDays(7)}
            className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            最近7天
          </button>
          <button
            onClick={() => setRecentDays(30)}
            className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            最近30天
          </button>
          <button
            onClick={() => setDateRange({ start: '', end: '' })}
            className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            全部
          </button>
          <div className="h-6 w-px bg-gray-300" />
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showConfidence}
              onChange={(e) => setShowConfidence(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">显示置信区间</span>
          </label>
        </div>
      </div>

      {/* 图表容器 */}
      <div className="relative">
        <div ref={chartRef} style={{ width: '100%', height }} />
        
        {/* 悬停信息卡片 */}
        {hoveredPoint && (
          <div className="absolute top-4 right-4 p-4 bg-white rounded-lg shadow-lg border border-gray-200 max-w-xs">
            <div className="flex items-center space-x-2 mb-2">
              <Info className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-semibold text-gray-700">数据详情</span>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">日期:</span>
                <span className="font-medium">{format(new Date(hoveredPoint.date), 'yyyy-MM-dd', { locale: zhCN })}</span>
              </div>
              {hoveredPoint.actual !== null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">实际:</span>
                  <span className="font-medium text-blue-600">${hoveredPoint.actual.toLocaleString()}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">预测:</span>
                <span className="font-medium text-green-600">${hoveredPoint.predicted.toLocaleString()}</span>
              </div>
              {hoveredPoint.actual !== null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">误差:</span>
                  <span className="font-medium">
                    {((Math.abs(hoveredPoint.actual - hoveredPoint.predicted) / hoveredPoint.actual) * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-600">平均准确率</span>
          </div>
          <div className="text-lg font-semibold text-gray-800">95.3%</div>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-600">预测趋势</span>
          </div>
          <div className="text-lg font-semibold text-gray-800">上升</div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="w-4 h-4 text-purple-500" />
            <span className="text-xs text-gray-600">最高预测</span>
          </div>
          <div className="text-lg font-semibold text-gray-800">$18.5k</div>
        </div>
        <div className="p-3 bg-orange-50 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="w-4 h-4 text-orange-500" />
            <span className="text-xs text-gray-600">预测周期</span>
          </div>
          <div className="text-lg font-semibold text-gray-800">7天</div>
        </div>
      </div>
    </div>
  );
};