# Price Breakdown Feature - Usage Guide

## Overview
A new endpoint has been added to provide energy price component breakdown data for doughnut chart visualization.

## API Endpoint

### `GET /api/price-breakdown`

Returns the breakdown of electricity price components based on the current wholesale market price.

**Response Structure:**
```json
{
  "labels": ["Generation & Wholesale", "Network Fees", "Taxes & Levies", "VAT (19%)", "Retail Margin"],
  "values": [40.0, 25.0, 20.0, 16.0, 7.0],
  "colors": ["#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#10b981"],
  "prices_eur_per_kwh": [0.08, 0.05, 0.04, 0.032, 0.014],
  "descriptions": ["...", "...", "...", "...", "..."],
  "total_price_eur_per_kwh": 0.1999,
  "wholesale_price_eur_per_mwh": 79.97,
  "wholesale_price_eur_per_kwh": 0.08,
  "note": "Component percentages are approximate...",
  "data_source": "Placeholder percentages - requires update with reliable source",
  "last_updated": null
}
```

## Frontend Integration Example (Chart.js)

```javascript
// Fetch price breakdown data
async function fetchPriceBreakdown() {
  const response = await fetch('http://localhost:8000/api/price-breakdown');
  const data = await response.json();
  return data;
}

// Create doughnut chart
async function createPriceBreakdownChart() {
  const breakdown = await fetchPriceBreakdown();
  
  const ctx = document.getElementById('priceBreakdownChart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: breakdown.labels,
      datasets: [{
        data: breakdown.values,
        backgroundColor: breakdown.colors,
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'right',
        },
        title: {
          display: true,
          text: `Energy Price Breakdown (Total: ${breakdown.total_price_eur_per_kwh} EUR/kWh)`
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const percentage = context.parsed;
              const price = breakdown.prices_eur_per_kwh[context.dataIndex];
              return `${label}: ${percentage}% (${price} EUR/kWh)`;
            },
            afterLabel: function(context) {
              return breakdown.descriptions[context.dataIndex];
            }
          }
        }
      }
    }
  });
}

// Initialize chart
createPriceBreakdownChart();
```

## Vue.js Example

```vue
<template>
  <div class="price-breakdown">
    <h3>Energy Price Components</h3>
    <canvas id="priceChart" ref="chartCanvas"></canvas>
    <div class="price-info">
      <p>Total Price: {{ breakdown.total_price_eur_per_kwh }} EUR/kWh</p>
      <p>Wholesale Price: {{ breakdown.wholesale_price_eur_per_mwh }} EUR/MWh</p>
      <p class="note">{{ breakdown.note }}</p>
    </div>
  </div>
</template>

<script>
import { Chart } from 'chart.js/auto';

export default {
  name: 'PriceBreakdown',
  data() {
    return {
      breakdown: null,
      chart: null
    };
  },
  async mounted() {
    await this.fetchBreakdown();
    this.createChart();
  },
  methods: {
    async fetchBreakdown() {
      const response = await fetch('http://localhost:8000/api/price-breakdown');
      this.breakdown = await response.json();
    },
    createChart() {
      const ctx = this.$refs.chartCanvas.getContext('2d');
      this.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: this.breakdown.labels,
          datasets: [{
            data: this.breakdown.values,
            backgroundColor: this.breakdown.colors,
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  const percentage = context.parsed;
                  const price = this.breakdown.prices_eur_per_kwh[context.dataIndex];
                  return `${context.label}: ${percentage}% (${price} EUR/kWh)`;
                }
              }
            }
          }
        }
      });
    }
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
  }
};
</script>
```

## Important Notes

⚠️ **UPDATE REQUIRED**: The current percentages are **placeholder values**. You need to update them with accurate data from a reliable source such as:

- **Bundesnetzagentur** (German Federal Network Agency)
- **BDEW** (Bundesverband der Energie- und Wasserwirtschaft)
- Official energy price composition statistics

### Where to Update Percentages

File: `src/core/forecasting/price_forecasting/EnergyPriceForecast.py`

Function: `get_price_breakdown()`

Look for the `components` dictionary around line 640 and update the percentage values:

```python
components = {
    'Generation & Wholesale': {
        'percentage': 40.0,  # UPDATE THIS
        'color': '#3b82f6',
        'description': 'Wholesale electricity market price'
    },
    'Network Fees': {
        'percentage': 25.0,  # UPDATE THIS
        # ...
    },
    # ... etc
}
```

## Testing

Test the endpoint using curl:
```bash
curl http://localhost:8000/api/price-breakdown
```

Or run the test script:
```bash
python3 test_price_breakdown.py
```

## Data Flow

1. Function checks for latest forecast file in `app_data/`
2. Calculates average wholesale price from forecast
3. Applies component percentages to calculate breakdown
4. Returns structured data ready for Chart.js doughnut chart

## Customization

You can also pass a custom wholesale price:
```python
from src.core.forecasting.price_forecasting.EnergyPriceForecast import get_price_breakdown

# Use custom price
breakdown = get_price_breakdown(avg_price_eur_per_mwh=120.0)
```
