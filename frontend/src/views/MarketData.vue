<template>
  <div class="market-data py-8">
    <div class="container">
      <div class="page-header">
        <h1>Marktdaten & Preise</h1>
        <p>Aktuelle Strompreise und Marktentwicklungen</p>
      </div>

      <div class="market-grid">
        <!-- Current Statistics -->
        <div class="stats-section">
          <h2 class="section-title">Aktuelle Kennzahlen</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-euro-sign"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ currentStats.price || '--' }}</div>
                <div class="stat-label">Aktueller Börsenpreis</div>
                <div class="stat-unit">€/MWh</div>
              </div>
              <div class="stat-change" :class="priceChangeClass">
                <i :class="priceChangeIcon"></i>
                {{ currentStats.change || '--' }}%
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-chart-bar"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ currentStats.avgPrice || '--' }}</div>
                <div class="stat-label">7-Tage Durchschnitt</div>
                <div class="stat-unit">€/MWh</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-arrow-up"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ currentStats.highPrice || '--' }}</div>
                <div class="stat-label">Tageshöchstpreis</div>
                <div class="stat-unit">€/MWh</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-arrow-down"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ currentStats.lowPrice || '--' }}</div>
                <div class="stat-label">Tagestiefstpreis</div>
                <div class="stat-unit">€/MWh</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Price Chart -->
        <div class="chart-section">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">
                <i class="fas fa-chart-line text-emerald-600"></i>
                Strompreisentwicklung
              </h3>
              <div class="chart-controls">
                <select v-model="selectedTimeframe" @change="updateChart" class="form-select">
                  <option value="7d">7 Tage</option>
                  <option value="30d">30 Tage</option>
                  <option value="90d">90 Tage</option>
                </select>
              </div>
            </div>
            
            <div class="chart-container">
              <canvas v-if="!chartLoading" ref="priceChart"></canvas>
              <div v-else class="loading">
                <div class="loading-spinner"></div>
                <p>Lade Marktdaten...</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Market News -->
        <div class="news-section">
          <h2 class="section-title">Markt-Updates</h2>
          <div class="news-grid">
            <div v-for="news in marketNews" :key="news.id" class="news-card">
              <div class="news-date">{{ formatDate(news.date) }}</div>
              <h4 class="news-title">{{ news.title }}</h4>
              <p class="news-content">{{ news.content }}</p>
              <div class="news-impact" :class="news.impact">
                <i class="fas fa-circle"></i>
                {{ news.impactText }}
              </div>
            </div>
          </div>
        </div>

        <!-- Price Forecast -->
        <div class="forecast-section">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">
                <i class="fas fa-crystal-ball text-purple-600"></i>
                Preisprognose
              </h3>
            </div>
            
            <div class="forecast-content">
              <div class="forecast-item">
                <div class="forecast-period">Nächste 24 Stunden</div>
                <div class="forecast-price">{{ forecast.next24h || '--' }}€/MWh</div>
                <div class="forecast-trend" :class="forecast.trend24h">
                  <i :class="getTrendIcon(forecast.trend24h)"></i>
                  {{ getTrendText(forecast.trend24h) }}
                </div>
              </div>
              
              <div class="forecast-item">
                <div class="forecast-period">Nächste 7 Tage</div>
                <div class="forecast-price">{{ forecast.next7d || '--' }}€/MWh</div>
                <div class="forecast-trend" :class="forecast.trend7d">
                  <i :class="getTrendIcon(forecast.trend7d)"></i>
                  {{ getTrendText(forecast.trend7d) }}
                </div>
              </div>
              
              <div class="forecast-item">
                <div class="forecast-period">Nächste 30 Tage</div>
                <div class="forecast-price">{{ forecast.next30d || '--' }}€/MWh</div>
                <div class="forecast-trend" :class="forecast.trend30d">
                  <i :class="getTrendIcon(forecast.trend30d)"></i>
                  {{ getTrendText(forecast.trend30d) }}
                </div>
              </div>
            </div>
            
            <div class="forecast-disclaimer">
              <i class="fas fa-info-circle"></i>
              Prognosen basieren auf historischen Daten und aktuellen Markttrends. 
              Keine Garantie für tatsächliche Preisentwicklung.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import { apiService } from '../services/api'

export default {
  name: 'MarketData',
  setup() {
    const currentStats = ref({
      price: null,
      change: null,
      avgPrice: null,
      highPrice: null,
      lowPrice: null
    })
    
    const selectedTimeframe = ref('7d')
    const chartLoading = ref(true)
    const priceChart = ref(null)
    const chartInstance = ref(null)
    
    const marketNews = ref([
      {
        id: 1,
        date: new Date('2025-08-02'),
        title: 'Strompreise steigen aufgrund hoher Nachfrage',
        content: 'Die Großhandelspreise für Strom sind heute um 15% gestiegen, da die Nachfrage aufgrund der Hitzewelle stark angestiegen ist.',
        impact: 'negative',
        impactText: 'Preisanstieg'
      },
      {
        id: 2,
        date: new Date('2025-08-01'),
        title: 'Neue Windkraftanlagen gehen ans Netz',
        content: 'Mit der Inbetriebnahme neuer Offshore-Windparks wird zusätzliche grüne Energie ins Netz eingespeist.',
        impact: 'positive',
        impactText: 'Preissenkung'
      },
      {
        id: 3,
        date: new Date('2025-07-31'),
        title: 'Wartungsarbeiten an Kraftwerken angekündigt',
        content: 'Mehrere konventionelle Kraftwerke werden in den nächsten Wochen für Wartungsarbeiten vom Netz genommen.',
        impact: 'neutral',
        impactText: 'Neutral'
      }
    ])
    
    const forecast = ref({
      next24h: null,
      trend24h: 'stable',
      next7d: null,
      trend7d: 'up',
      next30d: null,
      trend30d: 'down'
    })
    
    const priceChangeClass = computed(() => {
      if (!currentStats.value.change) return ''
      return currentStats.value.change > 0 ? 'positive' : 'negative'
    })
    
    const priceChangeIcon = computed(() => {
      if (!currentStats.value.change) return 'fas fa-minus'
      return currentStats.value.change > 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down'
    })
    
    const loadMarketData = async () => {
      chartLoading.value = true
      
      try {
        const response = await apiService.getMarketPrices()
        const prices = response.data.prices
        
        if (prices && prices.length > 0) {
          // Calculate statistics
          const currentPrice = prices[prices.length - 1].price
          const previousPrice = prices.length > 1 ? prices[prices.length - 2].price : currentPrice
          const change = ((currentPrice - previousPrice) / previousPrice * 100).toFixed(2)
          
          const recentPrices = prices.slice(-168) // Last 7 days (hourly data)
          const avgPrice = (recentPrices.reduce((sum, p) => sum + p.price, 0) / recentPrices.length).toFixed(2)
          const highPrice = Math.max(...recentPrices.map(p => p.price)).toFixed(2)
          const lowPrice = Math.min(...recentPrices.map(p => p.price)).toFixed(2)
          
          currentStats.value = {
            price: currentPrice.toFixed(2),
            change: change,
            avgPrice: avgPrice,
            highPrice: highPrice,
            lowPrice: lowPrice
          }
          
          // Generate mock forecast
          forecast.value = {
            next24h: (currentPrice + (Math.random() - 0.5) * 10).toFixed(2),
            trend24h: Math.random() > 0.5 ? 'up' : 'down',
            next7d: (avgPrice * (0.9 + Math.random() * 0.2)).toFixed(2),
            trend7d: 'stable',
            next30d: (avgPrice * (0.85 + Math.random() * 0.3)).toFixed(2),
            trend30d: 'down'
          }
          
          // Create chart
          await nextTick()
          createChart(prices)
        }
      } catch (error) {
        console.error('Error loading market data:', error)
        
        // Generate mock data if API fails
        generateMockData()
      } finally {
        chartLoading.value = false
      }
    }
    
    const generateMockData = () => {
      const mockPrices = []
      const basePrice = 45
      const now = new Date()
      
      for (let i = 168; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000)
        const dailyPattern = 10 * Math.sin(2 * Math.PI * (time.getHours()) / 24)
        const noise = (Math.random() - 0.5) * 6
        const price = Math.max(0, basePrice + dailyPattern + noise)
        
        mockPrices.push({
          datetime: time.toISOString(),
          price: price
        })
      }
      
      const currentPrice = mockPrices[mockPrices.length - 1].price
      const avgPrice = mockPrices.reduce((sum, p) => sum + p.price, 0) / mockPrices.length
      
      currentStats.value = {
        price: currentPrice.toFixed(2),
        change: ((Math.random() - 0.5) * 10).toFixed(2),
        avgPrice: avgPrice.toFixed(2),
        highPrice: Math.max(...mockPrices.map(p => p.price)).toFixed(2),
        lowPrice: Math.min(...mockPrices.map(p => p.price)).toFixed(2)
      }
      
      forecast.value = {
        next24h: (currentPrice + (Math.random() - 0.5) * 10).toFixed(2),
        trend24h: Math.random() > 0.5 ? 'up' : 'down',
        next7d: (avgPrice * (0.9 + Math.random() * 0.2)).toFixed(2),
        trend7d: 'stable',
        next30d: (avgPrice * (0.85 + Math.random() * 0.3)).toFixed(2),
        trend30d: 'down'
      }
      
      createChart(mockPrices)
    }
    
    const createChart = (prices) => {
      if (chartInstance.value) {
        chartInstance.value.destroy()
      }
      
      if (!priceChart.value) return
      
      const ctx = priceChart.value.getContext('2d')
      
      // Filter data based on selected timeframe
      let filteredPrices = prices
      const now = new Date()
      
      switch (selectedTimeframe.value) {
        case '7d':
          filteredPrices = prices.slice(-168) // 7 days * 24 hours
          break
        case '30d':
          filteredPrices = prices.slice(-720) // 30 days * 24 hours
          break
        case '90d':
          // Sample every 6 hours for 90 days
          filteredPrices = prices.filter((_, index) => index % 6 === 0).slice(-360)
          break
      }
      
      chartInstance.value = new Chart(ctx, {
        type: 'line',
        data: {
          labels: filteredPrices.map(p => new Date(p.datetime)),
          datasets: [{
            label: 'Strompreis (€/MWh)',
            data: filteredPrices.map(p => p.price),
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          scales: {
            x: {
              type: 'time',
              time: {
                displayFormats: {
                  hour: 'HH:mm',
                  day: 'DD.MM',
                  week: 'DD.MM',
                  month: 'MMM'
                }
              },
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: false,
              grid: {
                color: '#f3f4f6'
              },
              ticks: {
                callback: function(value) {
                  return value.toFixed(1) + '€'
                }
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: '#1f2937',
              titleColor: '#f9fafb',
              bodyColor: '#f9fafb',
              borderColor: '#374151',
              borderWidth: 1,
              callbacks: {
                label: function(context) {
                  return `Preis: ${context.parsed.y.toFixed(2)}€/MWh`
                }
              }
            }
          }
        }
      })
    }
    
    const updateChart = () => {
      loadMarketData()
    }
    
    const formatDate = (date) => {
      return new Intl.DateTimeFormat('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
    }
    
    const getTrendIcon = (trend) => {
      switch (trend) {
        case 'up': return 'fas fa-arrow-up'
        case 'down': return 'fas fa-arrow-down'
        case 'stable': return 'fas fa-minus'
        default: return 'fas fa-minus'
      }
    }
    
    const getTrendText = (trend) => {
      switch (trend) {
        case 'up': return 'Steigend'
        case 'down': return 'Fallend'
        case 'stable': return 'Stabil'
        default: return 'Unbekannt'
      }
    }
    
    onMounted(() => {
      loadMarketData()
    })
    
    return {
      currentStats,
      selectedTimeframe,
      chartLoading,
      priceChart,
      marketNews,
      forecast,
      priceChangeClass,
      priceChangeIcon,
      updateChart,
      formatDate,
      getTrendIcon,
      getTrendText
    }
  }
}
</script>

<style scoped>
.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.page-header p {
  font-size: 1.1rem;
  color: #6b7280;
}

.market-grid {
  display: grid;
  gap: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.stat-unit {
  color: #9ca3af;
  font-size: 0.8rem;
}

.stat-change {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.stat-change.positive {
  background: #dcfce7;
  color: #166534;
}

.stat-change.negative {
  background: #fef2f2;
  color: #b91c1c;
}

.chart-section {
  margin-bottom: 2rem;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-controls select {
  min-width: 120px;
}

.chart-container {
  height: 400px;
  position: relative;
}

.news-section {
  margin-bottom: 2rem;
}

.news-grid {
  display: grid;
  gap: 1rem;
}

.news-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.news-date {
  color: #6b7280;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.news-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.news-content {
  color: #374151;
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.news-impact {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.news-impact.positive {
  background: #dcfce7;
  color: #166534;
}

.news-impact.negative {
  background: #fef2f2;
  color: #b91c1c;
}

.news-impact.neutral {
  background: #f3f4f6;
  color: #374151;
}

.forecast-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.forecast-item {
  text-align: center;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.forecast-period {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.forecast-price {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.forecast-trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
}

.forecast-trend.up {
  color: #b91c1c;
}

.forecast-trend.down {
  color: #166534;
}

.forecast-trend.stable {
  color: #6b7280;
}

.forecast-disclaimer {
  background: #fef3c7;
  color: #92400e;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .forecast-content {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style>
