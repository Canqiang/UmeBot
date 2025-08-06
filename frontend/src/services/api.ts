// ============== src/services/api.ts ==============
import axios, { AxiosInstance } from 'axios';

// API配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    if (error.response) {
      // 服务器返回错误
      const message = error.response.data?.detail || error.response.data?.message || '请求失败';
      throw new Error(message);
    } else if (error.request) {
      // 请求未到达服务器
      throw new Error('网络错误，请检查网络连接');
    } else {
      throw new Error('请求配置错误');
    }
  }
);

// API方法
export const api = {
  // 获取日报
  getDailyReport: async () => {
    return apiClient.get('/api/daily-report');
  },

  // 运行分析
  runAnalysis: async (params: {
    start_date: string;
    end_date: string;
    analysis_type?: string;
  }) => {
    return apiClient.post('/api/analyze', params);
  },

  // 查询数据
  queryData: async (params: {
    question: string;
    context?: any[];
    filters?: any;
  }) => {
    return apiClient.post('/api/query', params);
  },

  // 获取预测
  getForecast: async (days: number = 7) => {
    return apiClient.get(`/api/forecast/${days}`);
  },

  // 获取详细数据
  getDetails: async (type: string, params: any) => {
    return apiClient.post('/api/details', { detail_type: type, params });
  },
};


