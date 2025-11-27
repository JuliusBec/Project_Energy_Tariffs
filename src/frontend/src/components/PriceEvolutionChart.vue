<template>
  <div class="price-evolution-chart">
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Lade Preisdaten...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
    </div>
    
    <div v-else class="chart-container">
      <div class="canvas-wrapper">
        <canvas ref="chartCanvas"></canvas>
      </div>
      
      <div class="chart-legend">
        <div class="legend-item">
          <span class="legend-color historical"></span>
          <span class="legend-text">Historische Preise</span>
        </div>
        <div class="legend-item">
          <span class="legend-color forecast"></span>
          <span class="legend-text">Prognose</span>
        </div>
        <div class="legend-item">
          <span class="legend-color confidence"></span>
          <span class="legend-text">95% Konfidenzintervall</span>
        </div>
      </div>
      
      <div class="chart-stats" v-if="metrics">
        <div class="stat-card">
          <div class="stat-label">Historischer Ø</div>
          <div class="stat-value">{{ metrics.avg_historical_price }} €/MWh</div>
          <div class="stat-period">{{ formatDateRange(metrics.historical_start_date, metrics.historical_end_date) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Prognose Ø</div>
          <div class="stat-value">{{ metrics.avg_forecast_price }} €/MWh</div>
          <div class="stat-period">{{ formatDateRange(metrics.forecast_start_date, metrics.forecast_end_date) }}</div>
        </div>
        <div class="stat-card" :class="{'trend-up': metrics.price_change_percentage > 0, 'trend-down': metrics.price_change_percentage < 0}">
          <div class="stat-label">Preisänderung</div>
          <div class="stat-value">
            <i :class="metrics.price_change_percentage > 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"></i>
            {{ Math.abs(metrics.price_change_percentage) }}%
          </div>
          <div class="stat-period">Erwartete Entwicklung</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { apiService } from '../services/api';

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default {
  name: 'PriceEvolutionChart',
  data() {
    return {
      loading: true,
      error: null,
      chartData: null,
      metrics: null,
      chart: null
    };
  },
  mounted() {
    this.loadChartData();
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
  },
  methods: {
    async loadChartData() {
      try {
        this.loading = true;
        this.error = null;
        
        const response = await apiService.getPriceChartData();
        const data = response.data;
        
        this.chartData = data;
        this.metrics = data.metrics;
        
        console.log('Data loaded successfully:', {
          hasHistorical: !!data.historical_data,
          hasForecast: !!data.forecast_data,
          hasCombined: !!data.combined_data,
          hasMetrics: !!data.metrics
        });
        
        // Set loading to false FIRST to render the canvas
        this.loading = false;
        
        // Wait for next tick to ensure canvas is rendered
        await this.$nextTick();
        
        // Add another small delay to ensure DOM is fully ready
        setTimeout(() => {
          console.log('Creating chart after nextTick, canvas ref:', !!this.$refs.chartCanvas);
          this.createChart();
        }, 100);
        
      } catch (err) {
        console.error('Error loading chart data:', err);
        this.error = 'Preisdaten konnten nicht geladen werden. Bitte versuchen Sie es später erneut.';
        this.loading = false;
      }
    },
    
    createChart() {
      if (!this.chartData || !this.$refs.chartCanvas) {
        console.error('Chart data or canvas ref not available');
        return;
      }
      
      console.log('Creating chart with data:', {
        historicalDays: this.chartData.historical_data.timestamps.length,
        forecastDays: this.chartData.forecast_data.timestamps.length,
        combinedDays: this.chartData.combined_data.timestamps.length
      });
      
      const ctx = this.$refs.chartCanvas.getContext('2d');
      const combined = this.chartData.combined_data;
      
      // Reduced subsampling to show every 3rd day for smoother chart
      const step = 3;
      
      // Find the transition point between historical and forecast
      const transitionIndex = combined.historical_prices.findIndex((p, i) => 
        p !== null && combined.forecast_prices[i + 1] !== null
      );
      
      // Create subsampled arrays, ensuring we include the transition point
      const labels = [];
      const historicalPrices = [];
      const forecastPrices = [];
      const forecastLower = [];
      const forecastUpper = [];
      
      for (let i = 0; i < combined.timestamps.length; i++) {
        // Include every nth point, plus points around the transition
        const includePoint = (i % step === 0) || 
                             (transitionIndex > 0 && Math.abs(i - transitionIndex) <= 1);
        
        if (includePoint) {
          labels.push(combined.timestamps[i]);
          historicalPrices.push(combined.historical_prices[i]);
          forecastPrices.push(combined.forecast_prices[i]);
          forecastLower.push(combined.forecast_lower[i]);
          forecastUpper.push(combined.forecast_upper[i]);
        }
      }
      
      console.log('Chart data prepared:', {
        labels: labels.length,
        historical: historicalPrices.filter(p => p !== null).length,
        forecast: forecastPrices.filter(p => p !== null).length,
        transitionIndex: transitionIndex
      });
      
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Historische Preise',
              data: historicalPrices,
              borderColor: 'rgb(5, 150, 105)',
              backgroundColor: 'rgba(5, 150, 105, 0.1)',
              borderWidth: 2,
              pointRadius: 0,
              pointHoverRadius: 4,
              tension: 0.4,
              fill: false
            },
            {
              label: 'Prognose',
              data: forecastPrices,
              borderColor: 'rgb(239, 68, 68)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 2,
              pointRadius: 0,
              pointHoverRadius: 4,
              tension: 0.4,
              borderDash: [5, 5],
              fill: false
            },
            {
              label: 'Oberes Konfidenzintervall',
              data: forecastUpper,
              borderColor: 'rgba(239, 68, 68, 0.2)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 1,
              pointRadius: 0,
              tension: 0.4,
              fill: '+1'
            },
            {
              label: 'Unteres Konfidenzintervall',
              data: forecastLower,
              borderColor: 'rgba(239, 68, 68, 0.2)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 1,
              pointRadius: 0,
              tension: 0.4,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            title: {
              display: true,
              text: 'Strompreisentwicklung und Prognose',
              font: {
                size: 16,
                weight: 'bold'
              },
              color: '#1f2937'
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null && context.parsed.y !== undefined) {
                    label += context.parsed.y.toFixed(2) + ' €/MWh';
                  }
                  return label;
                }
              }
            },
            legend: {
              display: false // We use custom legend
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
                  weight: 'bold'
                }
              },
              ticks: {
                maxRotation: 45,
                minRotation: 45,
                autoSkip: true,
                maxTicksLimit: 12
              }
            },
            y: {
              display: true,
              title: {
                display: true,
                text: 'Preis (€/MWh)',
                font: {
                  size: 12,
                  weight: 'bold'
                }
              },
              beginAtZero: false
            }
          }
        }
      });
    },
    
    formatDateRange(startDate, endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const options = { year: 'numeric', month: 'short' };
      return `${start.toLocaleDateString('de-DE', options)} - ${end.toLocaleDateString('de-DE', options)}`;
    }
  }
};
</script>

<style scoped>
.price-evolution-chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #6b7280;
}

.loading-state i {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #059669;
}

.error-state i {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #dc2626;
}

.loading-state p,
.error-state p {
  font-size: 1rem;
  margin: 0;
}

.chart-container {
  width: 100%;
}

.canvas-wrapper {
  width: 100%;
  height: 450px;
  position: relative;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  width: 20px;
  height: 3px;
  border-radius: 2px;
}

.legend-color.historical {
  background: rgb(5, 150, 105);
}

.legend-color.forecast {
  background: rgb(239, 68, 68);
}

.legend-color.confidence {
  background: rgba(239, 68, 68, 0.3);
  height: 12px;
}

.legend-text {
  font-size: 0.9rem;
  color: #4b5563;
}

.chart-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
}

.stat-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.stat-label {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.stat-period {
  font-size: 0.75rem;
  color: #9ca3af;
}

.trend-up .stat-value {
  color: #dc2626;
}

.trend-down .stat-value {
  color: #059669;
}

.stat-value i {
  font-size: 1.2rem;
  margin-right: 0.25rem;
}

@media (max-width: 768px) {
  .canvas-wrapper {
    height: 300px !important;
  }
  
  .chart-legend {
    gap: 1rem;
  }
  
  .chart-stats {
    grid-template-columns: 1fr;
  }
}
</style>
