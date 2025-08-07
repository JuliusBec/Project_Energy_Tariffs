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
  
  // Market data endpoints
  getMarketPrices: () => {
    return api.get('/market-prices')
  },
  
  // Tips endpoints
  getUsageTips: () => {
    return api.get('/usage-tips')
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
