<template>
  <div class="load-profile-chart-container">
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Lade Lastprofil-Daten...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>
    
    <div v-else-if="chartData" class="chart-content">
      <div class="chart-wrapper">
        <canvas ref="chartCanvas"></canvas>
      </div>
      
      <div class="chart-legend">
        <div class="legend-item">
          <span class="legend-color" style="background: #3b82f6;"></span>
          <span>Ihr durchschn. Verbrauch (kWh)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #f59e0b;"></span>
          <span>Durchschn. Preis (€/kWh)</span>
        </div>
      </div>
      
      <div class="chart-footer">
        <small>{{ summary.total_days_analyzed }} Tage analysiert | Korrelation: {{ (summary.correlation * 100).toFixed(0) }}%</small>
      </div>
    </div>
    
    <div v-else class="no-data-state">
      <i class="fas fa-chart-area"></i>
      <p>Keine Daten verfügbar</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'LoadProfileChart',
  props: {
    loadProfileData: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const loading = ref(false)
    const error = ref(null)
    const chartData = ref(null)
    const summary = ref(null)
    const chartCanvas = ref(null)
    let chartInstance = null
    
    const createChart = () => {
      if (!chartCanvas.value || !chartData.value) return
      
      // Destroy existing chart
      if (chartInstance) {
        chartInstance.destroy()
      }
      
      const ctx = chartCanvas.value.getContext('2d')
      
      // Extract data
      const hours = chartData.value.map(d => d.hour)
      const consumption = chartData.value.map(d => d.avg_consumption_kwh)
      const prices = chartData.value.map(d => d.avg_price_eur_per_kwh)
      
      // Find max values for scaling
      const maxConsumption = Math.max(...consumption)
      const maxPrice = Math.max(...prices)
      
      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: hours.map(h => `${h}:00`),
          datasets: [
            {
              label: 'Ihr durchschn. Verbrauch (kWh)',
              data: consumption,
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              fill: true,
              tension: 0.4,
              yAxisID: 'y',
              pointRadius: 3,
              pointHoverRadius: 5
            },
            {
              label: 'Preis (€/kWh)',
              data: prices,
              borderColor: '#f59e0b',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              borderWidth: 2,
              fill: true,
              tension: 0.4,
              yAxisID: 'y1',
              pointRadius: 3,
              pointHoverRadius: 5
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
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              titleFont: {
                size: 14,
                weight: 'bold'
              },
              bodyFont: {
                size: 13
              },
              callbacks: {
                title: (context) => {
                  return `${context[0].label} Uhr`
                },
                label: (context) => {
                  const label = context.dataset.label || ''
                  const value = context.parsed.y.toFixed(3)
                  return `${label}: ${value}`
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: true,
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                font: {
                  size: 11
                }
              }
            },
            y: {
              type: 'linear',
              display: true,
              position: 'left',
              title: {
                display: true,
                text: 'Ihr durchschn. Verbrauch (kWh)',
                font: {
                  size: 12,
                  weight: 'bold'
                },
                color: '#3b82f6'
              },
              grid: {
                display: true,
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                font: {
                  size: 11
                },
                color: '#3b82f6'
              }
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Preis (€/kWh)',
                font: {
                  size: 12,
                  weight: 'bold'
                },
                color: '#f59e0b'
              },
              grid: {
                drawOnChartArea: false
              },
              ticks: {
                font: {
                  size: 11
                },
                color: '#f59e0b'
              }
            }
          }
        }
      })
    }
    
    const loadData = () => {
      if (!props.loadProfileData) return
      
      try {
        chartData.value = props.loadProfileData.hourly_data
        summary.value = props.loadProfileData.summary
        
        // Create chart on next tick to ensure canvas is rendered
        setTimeout(() => createChart(), 0)
      } catch (err) {
        console.error('Error loading load profile data:', err)
        error.value = 'Fehler beim Laden der Daten'
      }
    }
    
    onMounted(() => {
      loadData()
    })
    
    watch(() => props.loadProfileData, () => {
      loadData()
    }, { deep: true })
    
    onBeforeUnmount(() => {
      if (chartInstance) {
        chartInstance.destroy()
      }
    })
    
    return {
      loading,
      error,
      chartData,
      summary,
      chartCanvas
    }
  }
}
</script>

<style scoped>
.load-profile-chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-state,
.error-state,
.no-data-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6b7280;
  min-height: 200px;
}

.loading-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #3b82f6;
}

.error-state {
  color: #ef4444;
}

.error-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.no-data-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.chart-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
}

.chart-wrapper {
  flex: 1;
  position: relative;
  min-height: 250px;
}

.chart-wrapper canvas {
  max-height: 300px;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  padding: 0.5rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #4b5563;
}

.legend-color {
  width: 20px;
  height: 3px;
  border-radius: 2px;
}

.chart-footer {
  text-align: center;
  padding: 0.5rem;
  color: #6b7280;
  font-size: 0.75rem;
  border-top: 1px solid #e5e7eb;
}
</style>
