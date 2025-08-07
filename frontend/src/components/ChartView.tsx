// frontend/src/components/ChartView.tsx
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { BarChart3, Download, Maximize2, Filter } from 'lucide-react';

interface ChartViewProps {
  data: {
    type: 'line' | 'bar' | 'pie' | 'scatter' | 'mixed' | 'area' | 'radar';
    title?: string;
    series: any[];
    xAxis?: any;
    yAxis?: any;
    options?: any;
  };
  onPointClick?: (params: any) => void;
  height?: string;
  showToolbar?: boolean;
}

export const ChartView: React.FC<ChartViewProps> = ({
  data,
  onPointClick,
  height = '400px',
  showToolbar = true
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartInstance, setChartInstance] = useState<echarts.ECharts | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedSeries, setSelectedSeries] = useState<string[]>([]);

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
      const option = buildChartOption(data);
      chartInstance.setOption(option);

      // 添加点击事件
      chartInstance.off('click');
      chartInstance.on('click', (params: any) => {
        if (onPointClick) {
          onPointClick(params);
        }

        // 高亮选中的数据点
        chartInstance.dispatchAction({
          type: 'highlight',
          seriesIndex: params.seriesIndex,
          dataIndex: params.dataIndex
        });
      });

      // 添加图例选择事件
      chartInstance.on('legendselectchanged', (params: any) => {
        const selected = Object.keys(params.selected).filter(key => params.selected[key]);
        setSelectedSeries(selected);
      });
    }
  }, [chartInstance, data, onPointClick]);

  const buildChartOption = (chartData: ChartViewProps['data']) => {
    const { type, title, series, xAxis, yAxis, options } = chartData;

    // 基础配置
    const baseOption: echarts.EChartsOption = {
      title: {
        text: title || '',
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
          color: '#1f2937'
        }
      },
      tooltip: {
        trigger: type === 'pie' ? 'item' : 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        padding: 12,
        textStyle: {
          color: '#374151',
          fontSize: 12
        },
        axisPointer: {
          type: 'cross',
          animation: true,
          label: {
            backgroundColor: '#6b7280'
          }
        },
        formatter: (params: any) => {
          if (type === 'pie') {
            return `
              <div style="font-weight: bold;">${params.name}</div>
              <div style="margin-top: 4px;">
                ${params.marker} ${params.seriesName}: ${params.value} (${params.percent}%)
              </div>
            `;
          }

          if (Array.isArray(params)) {
            let html = `<div style="font-weight: bold; margin-bottom: 8px;">${params[0].axisValue}</div>`;
            params.forEach((item: any) => {
              const value = typeof item.value === 'number'
                ? item.value.toLocaleString()
                : item.value;
              html += `
                <div style="display: flex; align-items: center; margin: 4px 0;">
                  ${item.marker}
                  <span style="margin: 0 8px; flex: 1;">${item.seriesName}:</span>
                  <span style="font-weight: bold;">${value}</span>
                </div>
              `;
            });
            return html;
          }

          return `${params.name}: ${params.value}`;
        }
      },
      legend: {
        bottom: 10,
        left: 'center',
        data: series.map(s => s.name),
        textStyle: {
          fontSize: 12,
          color: '#6b7280'
        },
        icon: 'circle',
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 15
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: title ? '15%' : '10%',
        containLabel: true
      },
      toolbox: showToolbar ? {
        feature: {
          dataZoom: {
            yAxisIndex: 'none',
            title: {
              zoom: '区域缩放',
              back: '缩放还原'
            }
          },
          dataView: {
            readOnly: false,
            title: '数据视图',
            lang: ['数据视图', '关闭', '刷新']
          },
          magicType: {
            type: ['line', 'bar', 'stack'],
            title: {
              line: '切换为折线图',
              bar: '切换为柱状图',
              stack: '切换为堆叠'
            }
          },
          restore: {
            title: '还原'
          },
          saveAsImage: {
            title: '保存为图片',
            pixelRatio: 2
          }
        },
        right: 20,
        top: 10
      } : undefined
    };

    // 根据图表类型构建特定配置
    if (type === 'pie') {
      return {
        ...baseOption,
        series: [{
          type: 'pie',
          radius: ['35%', '65%'],
          center: ['50%', '50%'],
          data: series,
          emphasis: {
            itemStyle: {
              shadowBlur: 20,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            },
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          label: {
            formatter: '{b}\n{d}%',
            fontSize: 11,
            color: '#6b7280'
          },
          labelLine: {
            lineStyle: {
              color: '#e5e7eb'
            }
          },
          itemStyle: {
            borderRadius: 4,
            borderColor: '#fff',
            borderWidth: 2
          }
        }],
        ...options
      };
    }

    if (type === 'radar') {
      return {
        ...baseOption,
        radar: {
          indicator: xAxis?.data?.map((name: string) => ({ name, max: 100 })) || [],
          shape: 'polygon',
          splitNumber: 4,
          axisName: {
            color: '#6b7280',
            fontSize: 11
          },
          splitLine: {
            lineStyle: {
              color: '#e5e7eb'
            }
          },
          splitArea: {
            show: true,
            areaStyle: {
              color: ['rgba(59, 130, 246, 0.05)', 'rgba(59, 130, 246, 0.1)']
            }
          },
          axisLine: {
            lineStyle: {
              color: '#e5e7eb'
            }
          }
        },
        series: series.map(s => ({
          ...s,
          type: 'radar',
          emphasis: {
            lineStyle: {
              width: 3
            }
          }
        })),
        ...options
      };
    }

    // 处理混合图表
    if (type === 'mixed') {
      return {
        ...baseOption,
        xAxis: xAxis || { type: 'category', data: [] },
        yAxis: [
          {
            type: 'value',
            name: '数值',
            position: 'left',
            axisLine: {
              show: true,
              lineStyle: {
                color: '#3b82f6'
              }
            },
            axisLabel: {
              color: '#6b7280',
              fontSize: 11
            },
            splitLine: {
              lineStyle: {
                color: '#f3f4f6',
                type: 'dashed'
              }
            }
          },
          {
            type: 'value',
            name: '百分比',
            position: 'right',
            axisLine: {
              show: true,
              lineStyle: {
                color: '#10b981'
              }
            },
            axisLabel: {
              color: '#6b7280',
              fontSize: 11,
              formatter: '{value}%'
            },
            splitLine: {
              show: false
            }
          }
        ],
        series: series.map((s, index) => ({
          ...s,
          yAxisIndex: s.yAxisIndex || (index > 0 ? 1 : 0),
          emphasis: {
            focus: 'series',
            blurScope: 'coordinateSystem'
          }
        })),
        ...options
      };
    }

    // 默认线图/柱图配置
    return {
      ...baseOption,
      xAxis: {
        type: 'category',
        data: xAxis?.data || [],
        boundaryGap: type === 'bar',
        axisLine: {
          lineStyle: {
            color: '#e5e7eb'
          }
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          rotate: xAxis?.rotate || 0,
          interval: xAxis?.interval || 'auto'
        },
        splitLine: {
          show: false
        },
        ...xAxis
      },
      yAxis: {
        type: 'value',
        name: yAxis?.name || '',
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
          formatter: yAxis?.formatter || '{value}'
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        },
        ...yAxis
      },
      dataZoom: series[0]?.data?.length > 20 ? [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          bottom: 40,
          height: 20
        }
      ] : undefined,
      series: series.map(s => ({
        ...s,
        type: s.type || type || 'line',
        smooth: s.smooth !== false && (s.type === 'line' || type === 'line'),
        symbol: s.symbol || 'circle',
        symbolSize: s.symbolSize || 6,
        itemStyle: {
          borderRadius: type === 'bar' ? [4, 4, 0, 0] : 0,
          ...s.itemStyle
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          },
          ...s.emphasis
        },
        areaStyle: s.areaStyle || (type === 'area' ? {
          opacity: 0.3,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: s.color || '#3b82f6' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.1)' }
          ])
        } : undefined),
        label: {
          show: s.showLabel || false,
          position: 'top',
          fontSize: 10,
          color: '#6b7280',
          ...s.label
        },
        ...s
      })),
      ...options
    };
  };

  const handleDownload = () => {
    if (chartInstance) {
      const url = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#ffffff'
      });
      const link = document.createElement('a');
      link.href = url;
      link.download = `chart_${Date.now()}.png`;
      link.click();
    }
  };

  const handleFullscreen = () => {
    if (!isFullscreen) {
      chartRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);

    // 等待全屏切换完成后重新渲染图表
    setTimeout(() => {
      chartInstance?.resize();
    }, 300);
  };

  const handleFilter = () => {
    // 可以添加筛选逻辑
    console.log('Filter clicked');
  };

  return (
    <div className="relative bg-white rounded-lg">
      {showToolbar && (
        <div className="absolute top-2 right-2 z-10 flex items-center space-x-2">
          <button
            onClick={handleFilter}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="筛选数据"
          >
            <Filter className="w-4 h-4" />
          </button>
          <button
            onClick={handleFullscreen}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="全屏"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            onClick={handleDownload}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="下载图表"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      )}

      <div
        ref={chartRef}
        style={{
          width: '100%',
          height: isFullscreen ? '100vh' : height,
          transition: 'height 0.3s ease'
        }}
      />

      {selectedSeries.length > 0 && (
        <div className="px-4 py-2 border-t text-xs text-gray-500">
          已选择: {selectedSeries.join(', ')}
        </div>
      )}
    </div>
  );
};