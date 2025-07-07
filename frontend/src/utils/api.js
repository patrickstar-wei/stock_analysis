import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 增加到2分钟，支持多周期分析
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API错误:', error);
    return Promise.reject(error);
  }
);

// 新的交易信号API函数
export const fetchTradingSignals = async (stockCode) => {
  try {
    const response = await api.post('/trading_signals', {
      stock_code: stockCode
    }, {
      timeout: 180000, // 3分钟超时，确保多周期分析有足够时间
    });
    return response.data;
  } catch (error) {
    console.error('获取交易信号失败:', error);
    throw error;
  }
};

export const stockAPI = {
  // 搜索股票
  searchStocks: async (query, limit = 10) => {
    try {
      const response = await api.get('/search_stocks', {
        params: { q: query, limit }
      });
      return response.data;
    } catch (error) {
      throw new Error('搜索股票失败');
    }
  },

  // 获取股票信息
  getStockInfo: async (codeOrName) => {
    try {
      const response = await api.get('/get_stock_info', {
        params: { code_or_name: codeOrName }
      });
      return response.data;
    } catch (error) {
      throw new Error('获取股票信息失败');
    }
  },

  // 生成交易信号
  generateTradingSignals: async (formData) => {
    try {
      const response = await api.post('/trading_signals', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3分钟超时，确保多周期分析有足够时间
      });
      return response.data;
    } catch (error) {
      throw new Error('生成交易信号失败');
    }
  },
};

export default api; 