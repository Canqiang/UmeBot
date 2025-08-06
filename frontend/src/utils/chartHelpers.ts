
// ============== src/utils/chartHelpers.ts ==============
export const chartHelpers = {
  // 生成渐变色
  createGradient: (chart: any, color1: string, color2: string) => {
    const gradient = chart.createLinearGradient(0, 0, 0, 1);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
  },

  // 默认图表配置
  getDefaultOptions: () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
    },
  }),

  // 颜色方案
  colorSchemes: {
    primary: ['#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE'],
    success: ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'],
    danger: ['#EF4444', '#F87171', '#FCA5A5', '#FECACA', '#FEE2E2'],
    warning: ['#F59E0B', '#FCD34D', '#FDE68A', '#FEF3C7', '#FFFBEB'],
    mixed: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
  },

  // 生成图表数据
  prepareChartData: (data: any[], labelKey: string, valueKey: string) => {
    return {
      labels: data.map(item => item[labelKey]),
      datasets: [{
        data: data.map(item => item[valueKey]),
        backgroundColor: chartHelpers.colorSchemes.primary,
      }],
    };
  },
};