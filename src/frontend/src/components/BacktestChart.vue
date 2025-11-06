<template>
  <div class="backtest-chart-container">
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Lade Backtest-Daten...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>
    
    <div v-else-if="chartData" class="chart-content">
      <div class="chart-header">
        <div class="chart-info">
          <span class="chart-period">{{ metrics.forecast_period_days }} Tage Backtest</span>
          <span class="chart-accuracy">{{ (100 - metrics.forecast_error_percentage).toFixed(1) }}% Genauigkeit</span>
        </div>
        <div class="header-controls">
          <label class="toggle-switch">
            <input type="checkbox" v-model="showDetailedView">
            <span class="toggle-slider">
              <span class="toggle-label-left">
                <i class="fas fa-calendar-day"></i>
                Täglich
              </span>
              <span class="toggle-label-right">
                <i class="fas fa-clock"></i>
                Stündlich
              </span>
            </span>
          </label>
          <button class="fullscreen-btn" @click="toggleFullscreen" :title="isFullscreen ? 'Vollbild beenden' : 'Vollbild'">
            <i :class="['fas', isFullscreen ? 'fa-compress' : 'fa-expand']"></i>
          </button>
        </div>
      </div>
      
      <div :class="['chart-wrapper', { fullscreen: isFullscreen }]">
        <button v-if="isFullscreen" class="close-fullscreen-btn" @click="toggleFullscreen" title="Vollbild beenden">
          <i class="fas fa-times"></i>
        </button>
        <canvas ref="chartCanvas"></canvas>
      </div>
      
      <div class="chart-metrics">
        <div class="metric-item">
          <span class="metric-label">Prognostiziert</span>
          <span class="metric-value">{{ metrics.total_forecast_usage.toFixed(1) }} kWh</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Tatsächlich</span>
          <span class="metric-value">{{ metrics.total_actual_usage.toFixed(1) }} kWh</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Abweichung</span>
          <span class="metric-value" :class="{ 'text-success': metrics.forecast_error_percentage < 5 }">
            {{ metrics.forecast_error_percentage.toFixed(1) }}%
          </span>
        </div>
      </div>
      
      <div class="chart-footer">
        <small>KI-basierte Verbrauchsprognose mit historischen Daten validiert</small>
      </div>
    </div>
    
    <div v-else class="no-data-state">
      <i class="fas fa-chart-line"></i>
      <p>Laden Sie Ihre Verbrauchsdaten hoch, um einen Backtest zu sehen</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import { apiService } from '../services/api'

Chart.register(...registerables)

export default {
  name: 'BacktestChart',
  props: {
    uploadedFile: {
      type: File,
      default: null
    }
  },
  setup(props) {
    const loading = ref(false)
    const error = ref(null)
    const chartData = ref(null)
    const hourlyData = ref(null)
    const dailyData = ref(null)
    const metrics = ref(null)
    const chartCanvas = ref(null)
    const showDetailedView = ref(false)
    const isFullscreen = ref(false)
    let chartInstance = null
    
    const toggleFullscreen = () => {
      isFullscreen.value = !isFullscreen.value
      // Re-render chart after fullscreen toggle to adjust size and aspect ratio
      setTimeout(() => {
        if (chartInstance) {
          // Update aspect ratio settings
          chartInstance.options.maintainAspectRatio = !isFullscreen.value
          chartInstance.options.aspectRatio = isFullscreen.value ? undefined : 2
          
          // Force chart to recalculate dimensions
          chartInstance.resize()
          
          // Additional resize after a short delay to ensure proper rendering
          setTimeout(() => {
            if (chartInstance) {
              chartInstance.resize()
            }
          }, 50)
        }
      }, 300) // Wait for CSS transition
    }
    
    const fetchBacktestData = async () => {
      if (!props.uploadedFile) {
        return
      }
      
      loading.value = true
      error.value = null
      
      try {
        const response = await apiService.getBacktestData(props.uploadedFile)
        const data = response.data
        console.log('Backtest data received:', data)
        
        dailyData.value = data.daily_data
        hourlyData.value = data.hourly_data
        chartData.value = data.daily_data // Start with daily view
        metrics.value = data.metrics
        
        // Wait for next tick to ensure canvas is rendered
        setTimeout(() => {
          renderChart()
        }, 0)
        
      } catch (err) {
        console.error('Error fetching backtest data:', err)
        error.value = 'Fehler beim Laden der Backtest-Daten. Bitte versuchen Sie es erneut.'
      } finally {
        loading.value = false
      }
    }
    
    const renderChart = () => {
      if (!chartCanvas.value || !dailyData.value || !hourlyData.value) {
        return
      }
      
      // Destroy existing chart if it exists
      if (chartInstance) {
        chartInstance.destroy()
      }
      
      const ctx = chartCanvas.value.getContext('2d')
      
      // Select data based on view mode
      const currentData = showDetailedView.value ? hourlyData.value : dailyData.value
      const isDetailed = showDetailedView.value
      
      // Build datasets
      const datasets = [
        {
          label: 'Tatsächlicher Verbrauch',
          data: currentData.actual,
          borderColor: '#f97316',
          backgroundColor: 'rgba(249, 115, 22, 0.1)',
          borderWidth: 2,
          pointRadius: isDetailed ? 0 : 2,
          pointHoverRadius: 4,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Prognose',
          data: currentData.forecast,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 2,
          pointRadius: isDetailed ? 0 : 2,
          pointHoverRadius: 4,
          tension: 0.3,
          fill: true,
          borderDash: [5, 5]
        }
      ]
      
      // Add confidence interval datasets for detailed view
      if (isDetailed && currentData.forecast_upper && currentData.forecast_lower) {
        datasets.push(
          {
            label: 'Obere Konfidenzgrenze (90%)',
            data: currentData.forecast_upper,
            borderColor: 'rgba(16, 185, 129, 0.3)',
            backgroundColor: 'rgba(16, 185, 129, 0.05)',
            borderWidth: 1,
            pointRadius: 0,
            tension: 0.3,
            fill: '+1',
            borderDash: [2, 2]
          },
          {
            label: 'Untere Konfidenzgrenze (90%)',
            data: currentData.forecast_lower,
            borderColor: 'rgba(16, 185, 129, 0.3)',
            backgroundColor: 'rgba(16, 185, 129, 0.05)',
            borderWidth: 1,
            pointRadius: 0,
            tension: 0.3,
            fill: false,
            borderDash: [2, 2]
          }
        )
      }
      
      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: currentData.timestamps,
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: !isFullscreen.value,
          aspectRatio: 2,
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: {
                usePointStyle: true,
                padding: 15,
                font: {
                  size: 12,
                  family: "'Inter', sans-serif"
                },
                filter: function(item) {
                  // Hide confidence bounds from legend in detailed view
                  if (isDetailed && item.text.includes('Konfidenzgrenze')) {
                    return false
                  }
                  return true
                }
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              titleFont: {
                size: 13,
                family: "'Inter', sans-serif"
              },
              bodyFont: {
                size: 12,
                family: "'Inter', sans-serif"
              },
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || ''
                  if (label) {
                    label += ': '
                  }
                  label += context.parsed.y.toFixed(2) + ' kWh'
                  return label
                }
              }
            }
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Datum',
                font: {
                  size: 12,
                  family: "'Inter', sans-serif"
                }
              },
              ticks: {
                maxRotation: 45,
                minRotation: 45,
                font: {
                  size: 10
                },
                autoSkip: true,
                maxTicksLimit: isDetailed ? 30 : 20,
                callback: function(value, index) {
                  // Format date to German format: dd.mm.yy
                  const dateStr = this.getLabelForValue(value)
                  const date = new Date(dateStr)
                  if (!isNaN(date.getTime())) {
                    const day = String(date.getDate()).padStart(2, '0')
                    const month = String(date.getMonth() + 1).padStart(2, '0')
                    const year = String(date.getFullYear()).slice(-2)
                    return `${day}.${month}.${year}`
                  }
                  return dateStr
                }
              },
              grid: {
                display: false
              }
            },
            y: {
              display: true,
              title: {
                display: true,
                text: isDetailed ? 'Stündlicher Verbrauch (kWh)' : 'Täglicher Verbrauch (kWh)',
                font: {
                  size: 12,
                  family: "'Inter', sans-serif"
                }
              },
              beginAtZero: true,
              ticks: {
                font: {
                  size: 10
                }
              },
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              }
            }
          }
        }
      })
    }
    
    // Watch for file changes
    watch(() => props.uploadedFile, (newFile) => {
      if (newFile) {
        fetchBacktestData()
      }
    })
    
    // Watch for view mode changes
    watch(showDetailedView, () => {
      renderChart()
    })
    
    onMounted(() => {
      if (props.uploadedFile) {
        fetchBacktestData()
      }
    })
    
    return {
      loading,
      error,
      chartData,
      metrics,
      chartCanvas,
      showDetailedView,
      isFullscreen,
      toggleFullscreen
    }
  }
}
</script>

<style scoped>
.backtest-chart-container {
  width: 100%;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-state,
.error-state,
.no-data-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
}

.loading-state i {
  font-size: 2.5rem;
  color: #2E86AB;
  margin-bottom: 1rem;
}

.error-state i {
  font-size: 2.5rem;
  color: #F24236;
  margin-bottom: 1rem;
}

.no-data-state i {
  font-size: 2.5rem;
  color: #999;
  margin-bottom: 1rem;
}

.chart-content {
  width: 100%;
}

.chart-header {
  margin-bottom: 1rem;
}

.chart-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 8px;
}

/* Toggle Switch Styles */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 220px;
  height: 44px;
  user-select: none;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f1f5f9;
  border-radius: 22px;
  transition: 0.3s;
  display: flex;
  align-items: center;
  padding: 4px;
  border: 1px solid #e2e8f0;
}

.toggle-slider::before {
  content: "";
  position: absolute;
  height: 36px;
  width: 106px;
  left: 4px;
  bottom: 3px;
  background: white;
  border-radius: 18px;
  transition: 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(106px);
}

.toggle-label-left,
.toggle-label-right {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.3s;
  z-index: 1;
  padding: 0 1rem;
}

.toggle-label-left {
  left: 0;
  color: #2E86AB;
}

.toggle-label-right {
  right: 0;
  color: #64748b;
}

.toggle-switch input:checked + .toggle-slider .toggle-label-left {
  color: #64748b;
}

.toggle-switch input:checked + .toggle-slider .toggle-label-right {
  color: #2E86AB;
}

.toggle-label-left i,
.toggle-label-right i {
  font-size: 0.875rem;
}

.fullscreen-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
}

.fullscreen-btn:hover {
  background: #f8fafc;
  color: #2E86AB;
  border-color: #cbd5e1;
}

.fullscreen-btn:active {
  transform: scale(0.95);
}

.close-fullscreen-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 50%;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1.25rem;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.close-fullscreen-btn:hover {
  background: #f8fafc;
  color: #ef4444;
  border-color: #fecaca;
  transform: scale(1.05);
}

.close-fullscreen-btn:active {
  transform: scale(0.95);
}

.chart-period {
  font-size: 0.875rem;
  color: #666;
  font-weight: 500;
}

.chart-accuracy {
  font-size: 0.875rem;
  color: #10b981;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
}

.chart-wrapper {
  position: relative;
  width: 100%;
  margin: 1rem 0;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.chart-wrapper canvas {
  width: 100% !important;
  height: auto !important;
  max-width: 100%;
}

.chart-wrapper.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  margin: 0;
  border-radius: 0;
  z-index: 9999;
  padding: 2rem;
  box-shadow: none;
  overflow: auto;
}

.chart-wrapper.fullscreen canvas {
  max-height: calc(100vh - 4rem);
  width: 100% !important;
  height: calc(100vh - 4rem) !important;
}

.chart-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0 1rem;
}

.metric-item {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.metric-label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.metric-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.text-success {
  color: #10b981 !important;
}

.chart-footer {
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.chart-footer small {
  color: #6b7280;
  font-size: 0.813rem;
}

@media (max-width: 768px) {
  .chart-wrapper {
    padding: 0.5rem;
  }
  
  .chart-wrapper.fullscreen {
    padding: 1rem;
  }
  
  .close-fullscreen-btn {
    top: 0.5rem;
    right: 0.5rem;
  }
  
  .chart-info {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .toggle-switch {
    flex: 1;
    max-width: 200px;
  }
  
  .chart-metrics {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .metric-item {
    padding: 0.75rem;
  }
}
</style>
