<template>
  <div class="price-breakdown-chart">
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Lade Preisdaten...</p>
    </div>
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>
    <div v-else class="chart-container">
      <canvas ref="chartCanvas"></canvas>
      <div class="chart-center-text">
        <div class="center-price">{{ formattedCenterPrice }}</div>
        <div class="center-label">Ø Preis/kWh</div>
      </div>
      <div class="chart-disclaimer">
        <i class="fas fa-info-circle"></i>
        <p>Informationen basieren auf Daten der Bundesnetzagentur. Die Aufschlüsselung ist nicht zwingend zu 100% genau.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, ArcElement, Tooltip, Legend } from 'chart.js';
import { apiService } from '../services/api';

// Register Chart.js components
Chart.register(ArcElement, Tooltip, Legend);

export default {
  name: 'PriceBreakdownChart',
  data() {
    return {
      loading: true,
      error: null,
      breakdown: null,
      chart: null
    };
  },
  computed: {
    formattedCenterPrice() {
      if (!this.breakdown) return '---';
      return `${this.breakdown.total_price_eur_per_kwh.toFixed(4)} €`;
    }
  },
  async mounted() {
    await this.fetchBreakdownData();
    if (this.breakdown) {
      this.createChart();
    }
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
  },
  methods: {
    async fetchBreakdownData() {
      try {
        this.loading = true;
        this.error = null;
        
        const response = await apiService.getPriceBreakdown();
        this.breakdown = response.data;
        
      } catch (err) {
        console.error('Error fetching price breakdown:', err);
        this.error = 'Preisdaten konnten nicht geladen werden';
      } finally {
        this.loading = false;
      }
    },
    createChart() {
      if (!this.$refs.chartCanvas || !this.breakdown) return;
      
      const ctx = this.$refs.chartCanvas.getContext('2d');
      
      this.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: this.breakdown.labels,
          datasets: [{
            data: this.breakdown.values,
            backgroundColor: this.breakdown.colors,
            borderWidth: 2,
            borderColor: '#ffffff',
            hoverBorderWidth: 3,
            hoverBorderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          cutout: '70%', // Makes it a doughnut with space in center
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 15,
                font: {
                  size: 12,
                  family: "'Inter', sans-serif"
                },
                usePointStyle: true,
                pointStyle: 'circle',
                generateLabels: (chart) => {
                  const data = chart.data;
                  if (data.labels.length && data.datasets.length) {
                    return data.labels.map((label, i) => {
                      const value = data.datasets[0].data[i];
                      const price = this.breakdown.prices_eur_per_kwh[i];
                      return {
                        text: `${label} (${value}%)`,
                        fillStyle: data.datasets[0].backgroundColor[i],
                        hidden: false,
                        index: i
                      };
                    });
                  }
                  return [];
                }
              }
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
                label: (context) => {
                  const label = context.label || '';
                  const percentage = context.parsed;
                  const price = this.breakdown.prices_eur_per_kwh[context.dataIndex];
                  return [
                    `${label}`,
                    `Anteil: ${percentage}%`,
                    `Preis: ${price.toFixed(4)} €/kWh`
                  ];
                },
                afterLabel: (context) => {
                  const description = this.breakdown.descriptions[context.dataIndex];
                  return `\n${description}`;
                }
              }
            }
          },
          animation: {
            animateRotate: true,
            animateScale: true,
            duration: 1000,
            easing: 'easeInOutQuart'
          }
        }
      });
    }
  }
};
</script>

<style scoped>
.price-breakdown-chart {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #64748b;
  text-align: center;
}

.loading-state i {
  font-size: 2.5rem;
  color: #059669;
}

.error-state i {
  font-size: 2.5rem;
  color: #dc2626;
}

.chart-container {
  position: relative;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.chart-center-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}

.center-price {
  font-size: 1.8rem;
  font-weight: 700;
  color: #059669;
  line-height: 1.2;
  margin-bottom: 0.25rem;
}

.center-label {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chart-disclaimer {
  margin-top: 1.5rem;
  padding: 0.75rem 1rem;
  background-color: #f1f5f9;
  border-left: 3px solid #059669;
  border-radius: 0.375rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: #475569;
  line-height: 1.5;
}

.chart-disclaimer i {
  color: #059669;
  font-size: 0.875rem;
  margin-top: 0.125rem;
  flex-shrink: 0;
}

.chart-disclaimer p {
  margin: 0;
}

@media (max-width: 768px) {
  .chart-container {
    max-width: 320px;
  }
  
  .center-price {
    font-size: 1.4rem;
  }
  
  .center-label {
    font-size: 0.75rem;
  }
  
  .chart-disclaimer {
    font-size: 0.7rem;
    padding: 0.625rem 0.875rem;
  }
}
</style>
