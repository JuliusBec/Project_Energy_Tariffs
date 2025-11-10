import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 120000,  // 120 seconds for CSV processing and scraping
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

  // New integrated endpoint: CSV + PLZ + Scraper
  compareTariffsWithCsv: (file, zipCode, providers = ['tibber', 'enbw']) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('zip_code', zipCode)
    formData.append('providers', providers.join(','))
    return api.post('/compare-tariffs-with-csv', formData, {
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
  
  // Scraper endpoints for real-time tariff data
  scrapeEnbwTariff: (zipCode, annualConsumption, options = {}) => {
    return api.post('/scrape/enbw', {
      zip_code: zipCode,
      annual_consumption: annualConsumption,
      headless: options.headless !== false,
      debug_mode: options.debug_mode || false
    }, {
      timeout: 90000  // 90 seconds for scraping
    })
  },
  
  scrapeTadoTariff: (zipCode, annualConsumption, options = {}) => {
    return api.post('/scrape/tado', {
      zip_code: zipCode,
      annual_consumption: annualConsumption,
      headless: options.headless !== false,
      debug_mode: options.debug_mode || false
    }, {
      timeout: 120000  // 120 seconds
    })
  },
  
  scrapeTibberTariff: (zipCode, annualConsumption, options = {}) => {
    return api.post('/scrape/tibber', {
      zip_code: zipCode,
      annual_consumption: annualConsumption,
      headless: options.headless !== undefined ? options.headless : true,
      debug_mode: options.debugMode || false
    }, {
      timeout: 120000  // 120 seconds
    })
  },
  
  // Combined scraper endpoint - returns all tariffs in EnergyTariff format
  scrapeAllTariffs: (zipCode, annualConsumption, providers = ['enbw', 'tado', 'tibber'], options = {}) => {
    return api.post('/scrape/tariffs', {
      zip_code: zipCode,
      annual_consumption: annualConsumption,
      providers: providers,
      headless: options.headless !== false,
      debug_mode: options.debug_mode || false
    }, {
      timeout: 180000  // 180 seconds for all scrapers
    })
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
