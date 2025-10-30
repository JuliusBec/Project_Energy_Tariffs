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
      </div>
      
      <div class="chart-wrapper">
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
    const metrics = ref(null)
    const chartCanvas = ref(null)
    let chartInstance = null
    
    const fetchBacktestData = async () => {
      if (!props.uploadedFile) {
        return
      }
      
      loading.value = true
      error.value = null
      
      try {
        const formData = new FormData()
        formData.append('file', props.uploadedFile)
        
        const response = await fetch('http://localhost:8000/api/backtest-data', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('Backtest data received:', data)
        
        chartData.value = data.daily_data
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
      if (!chartCanvas.value || !chartData.value) {
        return
      }
      
      // Destroy existing chart if it exists
      if (chartInstance) {
        chartInstance.destroy()
      }
      
      const ctx = chartCanvas.value.getContext('2d')
      
      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: chartData.value.timestamps,
          datasets: [
            {
              label: 'Tatsächlicher Verbrauch',
              data: chartData.value.actual,
              borderColor: '#F24236',
              backgroundColor: 'rgba(242, 66, 54, 0.1)',
              borderWidth: 2,
              pointRadius: 4,
              pointHoverRadius: 6,
              tension: 0.3,
              fill: true
            },
            {
              label: 'Prognose',
              data: chartData.value.forecast,
              borderColor: '#2E86AB',
              backgroundColor: 'rgba(46, 134, 171, 0.1)',
              borderWidth: 2,
              pointRadius: 4,
              pointHoverRadius: 6,
              tension: 0.3,
              fill: true,
              borderDash: [5, 5]
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
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
                text: 'Täglicher Verbrauch (kWh)',
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
      chartCanvas
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
  
  .chart-metrics {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .metric-item {
    padding: 0.75rem;
  }
}
</style>
