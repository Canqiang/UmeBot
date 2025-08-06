// ============== src/utils/dataProcessor.ts ==============
export const dataProcessor = {
  // 聚合数据
  aggregate: (data: any[], groupBy: string, aggregateField: string, method: 'sum' | 'avg' | 'count' = 'sum') => {
    const grouped = data.reduce((acc, item) => {
      const key = item[groupBy];
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(item[aggregateField]);
      return acc;
    }, {} as Record<string, number[]>);

    return Object.entries(grouped).map(([key, values]) => {
      let result = 0;
      switch (method) {
        case 'sum':
          result = values.reduce((a, b) => a + b, 0);
          break;
        case 'avg':
          result = values.reduce((a, b) => a + b, 0) / values.length;
          break;
        case 'count':
          result = values.length;
          break;
      }
      return { [groupBy]: key, value: result };
    });
  },

  // 计算变化率
  calculateChange: (current: number, previous: number): number => {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  },

  // 排序
  sortData: (data: any[], field: string, direction: 'asc' | 'desc' = 'desc') => {
    return [...data].sort((a, b) => {
      if (direction === 'asc') {
        return a[field] > b[field] ? 1 : -1;
      } else {
        return a[field] < b[field] ? 1 : -1;
      }
    });
  },

  // 过滤
  filterData: (data: any[], filters: Record<string, any>) => {
    return data.filter(item => {
      return Object.entries(filters).every(([key, value]) => {
        if (Array.isArray(value)) {
          return value.includes(item[key]);
        }
        return item[key] === value;
      });
    });
  },

  // 分页
  paginate: (data: any[], page: number, pageSize: number) => {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return {
      data: data.slice(start, end),
      total: data.length,
      totalPages: Math.ceil(data.length / pageSize),
      currentPage: page,
    };
  },
};