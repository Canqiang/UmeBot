// ============== src/utils/format.ts ==============
export const formatUtils = {
  // 格式化货币
  currency: (value: number | string, currency = 'USD'): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(num);
  },

  // 格式化百分比
  percentage: (value: number, decimals = 1): string => {
    return `${(value * 100).toFixed(decimals)}%`;
  },

  // 格式化数字
  number: (value: number | string): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US').format(num);
  },

  // 格式化日期
  date: (date: string | Date, format = 'short'): string => {
    const d = typeof date === 'string' ? new Date(date) : date;

    if (format === 'short') {
      return d.toLocaleDateString('zh-CN');
    } else if (format === 'long') {
      return d.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } else if (format === 'time') {
      return d.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } else {
      return d.toLocaleString('zh-CN');
    }
  },

  // 格式化时间差
  timeAgo: (date: string | Date): string => {
    const d = typeof date === 'string' ? new Date(date) : date;
    const now = new Date();
    const seconds = Math.floor((now.getTime() - d.getTime()) / 1000);

    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}天前`;
    return d.toLocaleDateString('zh-CN');
  },

  // 缩写大数字
  abbreviateNumber: (value: number): string => {
    if (value < 1000) return value.toString();
    if (value < 1000000) return `${(value / 1000).toFixed(1)}K`;
    if (value < 1000000000) return `${(value / 1000000).toFixed(1)}M`;
    return `${(value / 1000000000).toFixed(1)}B`;
  },
};