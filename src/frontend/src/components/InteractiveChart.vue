<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>{{ title }}</h3>
      <div class="chart-controls">
        <button 
          @click="showDaily = true" 
          :class="{ active: showDaily }"
          class="btn btn-sm"
        >
          Daily View
        </button>
        <button 
          @click="showDaily = false" 
          :class="{ active: !showDaily }"
          class="btn btn-sm"
        >
          Hourly View
        </button>
      </div>
    </div>
    
    <div class="metrics-summary" v-if="metrics">
      <div class="metric">
        <span class="metric-label">Total Actual Usage:</span>
        <span class="metric-value">{{ metrics.total_actual_usage?.toFixed(2) }} kWh</span>
      </div>
      <div class="metric">
        <span class="metric-label">Total Forecast Usage:</span>
        <span class="metric-value">{{ metrics.total_forecast_usage?.toFixed(2) }} kWh</span>
      </div>
      <div class="metric">
        <span class="metric-label">Forecast Error:</span>
        <span class="metric-value">{{ metrics.forecast_error_percentage?.toFixed(1) }}%</span>
      </div>
      <div class="metric">
        <span class="metric-label">MAE:</span>
        <span class="metric-value">{{ metrics.mae?.toFixed(4) }}</span>
      </div>
    </div>
    
    <div class="chart-wrapper">
      <Line
        v-if="chartData"
        :data="chartData"
        :options="chartOptions"
        :key="chartKey"
      />
      <div v-else class="loading-chart">
        <div class="loading-spinner"></div>
        <p>Loading chart data...</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

export default {
  name: 'InteractiveChart',
  components: {
    Line
  },
  props: {
    title: {
      type: String,
      default: 'Energy Usage Backtest'
    },
    hourlyData: {
      type: Object,
      required: true
    },
    dailyData: {
      type: Object,
      required: true
    },
    metrics: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const showDaily = ref(true)
    const chartKey = ref(0)

    const chartData = computed(() => {
      if (!props.hourlyData || !props.dailyData) return null
      
      const data = showDaily.value ? props.dailyData : props.hourlyData
      
      const datasets = [
        {
          label: 'Actual Usage',
          data: data.actual,
          borderColor: '#F24236',
          backgroundColor: 'rgba(242, 66, 54, 0.1)',
          borderWidth: 2,
          pointRadius: showDaily.value ? 4 : 1,
          pointHoverRadius: 6,
          tension: 0.1
        },
        {
          label: 'Forecast',
          data: data.forecast,
          borderColor: '#2E86AB',
          backgroundColor: 'rgba(46, 134, 171, 0.1)',
          borderWidth: 2,
          pointRadius: showDaily.value ? 4 : 1,
          pointHoverRadius: 6,
          tension: 0.1,
          borderDash: [5, 5]
        }
      ]

      // Add confidence interval for hourly view
      if (!showDaily.value && props.hourlyData.forecast_lower && props.hourlyData.forecast_upper) {
        datasets.push({
          label: '90% Confidence Interval',
          data: data.forecast_upper,
          borderColor: 'rgba(46, 134, 171, 0.2)',
          backgroundColor: 'rgba(46, 134, 171, 0.1)',
          borderWidth: 0,
          pointRadius: 0,
          fill: '+1',
          tension: 0.1
        })
        datasets.push({
          label: 'Lower Bound',
          data: data.forecast_lower,
          borderColor: 'rgba(46, 134, 171, 0.2)',
          backgroundColor: 'rgba(46, 134, 171, 0.1)',
          borderWidth: 0,
          pointRadius: 0,
          fill: false,
          tension: 0.1
        })
      }

      return {
        labels: data.timestamps,
        datasets
      }
    })

    const chartOptions = computed(() => ({
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        title: {
          display: true,
          text: `${showDaily.value ? 'Daily' : 'Hourly'} Energy Usage: Actual vs Forecast`,
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        legend: {
          display: true,
          position: 'top',
          labels: {
            filter: (legendItem) => {
              // Hide confidence interval bounds from legend
              return !legendItem.text.includes('Lower Bound')
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: 'white',
          bodyColor: 'white',
          borderColor: 'rgba(255, 255, 255, 0.3)',
          borderWidth: 1,
          callbacks: {
            label: function(context) {
              const value = context.parsed.y.toFixed(3)
              return `${context.dataset.label}: ${value} kWh`
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: showDaily.value ? 'Date' : 'Date and Time'
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.1)'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: `${showDaily.value ? 'Daily' : 'Hourly'} Energy Usage (kWh)`
          },
          beginAtZero: true,
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.1)'
          }
        }
      },
      elements: {
        point: {
          hoverBackgroundColor: 'white',
          hoverBorderWidth: 2
        }
      }
    }))

    // Force chart re-render when switching views
    watch(showDaily, () => {
      chartKey.value++
    })

    return {
      showDaily,
      chartData,
      chartOptions,
      chartKey
    }
  }
}
</script>

<style scoped>
.chart-container {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.chart-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.chart-controls {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:hover {
  background: #f9fafb;
}

.btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.metrics-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1f2937;
}

.chart-wrapper {
  height: 400px;
  position: relative;
}

.loading-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .chart-container {
    padding: 1rem;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .chart-controls {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  
  .metrics-summary {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper {
    height: 300px;
  }
}
</style>