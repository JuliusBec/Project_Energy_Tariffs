import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      // Redirect to login if needed
    }
    return Promise.reject(error)
  }
)

export const apiService = {
  // Tariff related endpoints
  getTariffs: (params = {}) => {
    return api.get('/tariffs', { params })
  },
  
  calculateTariffs: (data) => {
    return api.post('/calculate', data)
  },
  
  calculateWithCsv: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/calculate-with-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // Market data endpoints
  getMarketPrices: () => {
    return api.get('/market-prices')
  },
  
  // Forecast endpoints
  getForecast: () => {
    return api.get('/forecast')
  },
  
  predictSavings: (data) => {
    return api.post('/predict-savings', data)
  },
  
  // Tips endpoints
  getUsageTips: () => {
    return api.get('/usage-tips')
  },

  // Backtest data endpoints
  getBacktestData: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/backtest-data', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // Risk analysis endpoints
  getRiskAnalysis: (file, days = 30) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('days', days)
    return api.post('/risk-analysis', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // Chart data endpoints
  getPriceChartData: () => {
    return api.get('/price-chart-data')
  },
  
  getPriceBreakdown: () => {
    return api.get('/price-breakdown')
  },
  
  // Generic request method
  request: (method, url, data = null, config = {}) => {
    return api.request({
      method,
      url,
      data,
      ...config
    })
  }
}

export default api
