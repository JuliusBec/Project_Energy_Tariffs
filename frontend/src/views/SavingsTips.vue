<template>
  <div class="savings-tips py-8">
    <div class="container">
      <div class="page-header">
        <h1>Energie-Spartipps</h1>
        <p>Reduzieren Sie Ihren Stromverbrauch und sparen Sie Geld</p>
      </div>

      <!-- Savings Calculator -->
      <section class="savings-calculator mb-8">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">
              <i class="fas fa-calculator text-green-600"></i>
              Sparpotenzial-Rechner
            </h2>
            <p>Berechnen Sie, wie viel Sie durch verschiedene Maßnahmen sparen können</p>
          </div>
          
          <div class="calculator-grid">
            <div class="calculator-form">
              <div class="form-group">
                <label class="form-label">Ihr aktueller Jahresverbrauch (kWh)</label>
                <input 
                  type="number" 
                  v-model="calculator.annualKwh" 
                  class="form-input"
                  placeholder="z.B. 3500"
                  min="1000"
                  max="20000"
                  @input="calculateSavings"
                >
              </div>
              
              <div class="form-group">
                <label class="form-label">Aktueller Strompreis (€/kWh)</label>
                <input 
                  type="number" 
                  v-model="calculator.currentPrice" 
                  class="form-input"
                  placeholder="z.B. 0.32"
                  step="0.01"
                  min="0"
                  max="1"
                  @input="calculateSavings"
                >
              </div>
            </div>
            
            <div class="savings-result" v-if="totalSavings > 0">
              <div class="total-savings">
                <div class="savings-amount">{{ totalSavings }}€</div>
                <div class="savings-label">Jährliches Sparpotenzial</div>
              </div>
              <div class="savings-breakdown">
                <div class="breakdown-item" v-for="tip in activeTips" :key="tip.id">
                  <span class="breakdown-name">{{ tip.category }}</span>
                  <span class="breakdown-amount">{{ tip.calculatedSavings }}€</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tips Categories -->
      <section class="tips-categories mb-8">
        <div class="category-tabs">
          <button 
            v-for="category in categories" 
            :key="category.id"
            @click="selectedCategory = category.id"
            class="category-tab"
            :class="{ active: selectedCategory === category.id }"
          >
            <i :class="category.icon"></i>
            <span>{{ category.name }}</span>
          </button>
        </div>
      </section>

      <!-- Tips Grid -->
      <section class="tips-grid">
        <div 
          v-for="tip in filteredTips" 
          :key="tip.id"
          class="tip-card"
          :class="{ active: activeTipIds.includes(tip.id) }"
        >
          <div class="tip-header">
            <div class="tip-icon" :style="{ backgroundColor: tip.color }">
              <i :class="tip.icon"></i>
            </div>
            <div class="tip-meta">
              <div class="tip-category">{{ tip.category }}</div>
              <div class="tip-difficulty" :class="tip.difficulty">
                {{ getDifficultyText(tip.difficulty) }}
              </div>
            </div>
            <div class="tip-toggle">
              <label class="switch">
                <input 
                  type="checkbox" 
                  :checked="activeTipIds.includes(tip.id)"
                  @change="toggleTip(tip.id)"
                >
                <span class="slider"></span>
              </label>
            </div>
          </div>
          
          <h3 class="tip-title">{{ tip.title }}</h3>
          <p class="tip-description">{{ tip.description }}</p>
          
          <div class="tip-details">
            <div class="detail-item">
              <i class="fas fa-euro-sign"></i>
              <span>{{ tip.potential_savings }}</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-chart-line"></i>
              <span>{{ tip.reduction }}% weniger Verbrauch</span>
            </div>
            <div class="detail-item">
              <i class="fas fa-clock"></i>
              <span>{{ tip.implementation_time }}</span>
            </div>
          </div>
          
          <div v-if="tip.steps" class="tip-steps">
            <h4>Umsetzung:</h4>
            <ol>
              <li v-for="step in tip.steps" :key="step">{{ step }}</li>
            </ol>
          </div>
          
          <div v-if="tip.tools" class="tip-tools">
            <h4>Benötigte Hilfsmittel:</h4>
            <ul>
              <li v-for="tool in tip.tools" :key="tool">{{ tool }}</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Energy Monitor Recommendation -->
      <section class="monitor-recommendation py-8 bg-gray-50">
        <div class="container">
          <div class="recommendation-content">
            <div class="recommendation-info">
              <h2>Empfehlung: Energieverbrauchs-Monitor</h2>
              <p>
                Mit einem intelligenten Energiemonitor können Sie Ihren Verbrauch in Echtzeit überwachen 
                und weitere Einsparpotenziale identifizieren.
              </p>
              <ul class="benefits-list">
                <li><i class="fas fa-check text-green-600"></i> Echtzeit Verbrauchsanzeige</li>
                <li><i class="fas fa-check text-green-600"></i> Automatische Geräteerkennung</li>
                <li><i class="fas fa-check text-green-600"></i> Detaillierte Verbrauchsanalyse</li>
                <li><i class="fas fa-check text-green-600"></i> Smartphone App inklusive</li>
              </ul>
            </div>
            
            <div class="recommendation-card">
              <div class="product-image">
                <i class="fas fa-plug fa-4x text-emerald-600"></i>
              </div>
              <h3>Smart Energy Monitor</h3>
              <div class="price">ab 89€</div>
              <div class="savings-potential">
                Sparpotenzial: bis zu 200€/Jahr
              </div>
              <button class="btn btn-primary w-full">
                <i class="fas fa-external-link-alt"></i>
                Mehr erfahren
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { apiService } from '../services/api'

export default {
  name: 'SavingsTips',
  setup() {
    const calculator = ref({
      annualKwh: 3500,
      currentPrice: 0.32
    })
    
    const selectedCategory = ref('all')
    const activeTipIds = ref([])
    
    const categories = ref([
      { id: 'all', name: 'Alle', icon: 'fas fa-th-large' },
      { id: 'heating', name: 'Heizen', icon: 'fas fa-thermometer-half' },
      { id: 'appliances', name: 'Geräte', icon: 'fas fa-tv' },
      { id: 'lighting', name: 'Beleuchtung', icon: 'fas fa-lightbulb' },
      { id: 'cooling', name: 'Kühlung', icon: 'fas fa-snowflake' },
      { id: 'water', name: 'Warmwasser', icon: 'fas fa-tint' },
      { id: 'smart', name: 'Smart Home', icon: 'fas fa-home' }
    ])
    
    const tips = ref([
      {
        id: 1,
        category: 'Heizen',
        categoryId: 'heating',
        title: 'Raumtemperatur um 1°C senken',
        description: 'Jedes Grad weniger spart etwa 6% der Heizkosten. Schon 1°C weniger macht einen spürbaren Unterschied.',
        potential_savings: '120-200€/Jahr',
        reduction: 6,
        implementation_time: 'Sofort',
        difficulty: 'easy',
        icon: 'fas fa-thermometer-half',
        color: '#ef4444',
        steps: [
          'Thermostat um 1°C herunterdrehen',
          'Warme Kleidung anziehen',
          'Nach einer Woche Verbrauch prüfen'
        ]
      },
      {
        id: 2,
        category: 'Beleuchtung',
        categoryId: 'lighting',
        title: 'LED-Lampen verwenden',
        description: 'LED-Lampen verbrauchen bis zu 80% weniger Strom als herkömmliche Glühbirnen und halten 25x länger.',
        potential_savings: '50-100€/Jahr',
        reduction: 15,
        implementation_time: '1-2 Stunden',
        difficulty: 'easy',
        icon: 'fas fa-lightbulb',
        color: '#f59e0b',
        steps: [
          'Alte Glühbirnen identifizieren',
          'Passende LED-Lampen kaufen',
          'Glühbirnen austauschen',
          'Alte Lampen fachgerecht entsorgen'
        ],
        tools: ['LED-Lampen', 'eventuell Leiter']
      },
      {
        id: 3,
        category: 'Geräte',
        categoryId: 'appliances',
        title: 'Standby-Verbrauch eliminieren',
        description: 'Schalten Sie Geräte komplett aus statt sie im Standby-Modus zu lassen. Verwenden Sie schaltbare Steckdosenleisten.',
        potential_savings: '30-70€/Jahr',
        reduction: 8,
        implementation_time: '30 Minuten',
        difficulty: 'easy',
        icon: 'fas fa-power-off',
        color: '#10b981',
        steps: [
          'Schaltbare Steckdosenleisten kaufen',
          'Gerätegruppen identifizieren',
          'Steckdosenleisten installieren',
          'Abends alle Geräte ausschalten'
        ],
        tools: ['Schaltbare Steckdosenleisten']
      },
      {
        id: 4,
        category: 'Kühlung',
        categoryId: 'cooling',
        title: 'Kühlschrank optimal einstellen',
        description: 'Kühlschrank auf 7°C und Gefrierschrank auf -18°C einstellen. Jedes Grad kälter erhöht den Verbrauch um 5%.',
        potential_savings: '25-50€/Jahr',
        reduction: 5,
        implementation_time: '5 Minuten',
        difficulty: 'easy',
        icon: 'fas fa-snowflake',
        color: '#3b82f6',
        steps: [
          'Kühlschrank-Thermometer besorgen',
          'Temperatur messen',
          'Thermostat entsprechend einstellen',
          'Nach 24h erneut messen'
        ],
        tools: ['Kühlschrank-Thermometer']
      },
      {
        id: 5,
        category: 'Warmwasser',
        categoryId: 'water',
        title: 'Waschen bei 30°C',
        description: 'Moderne Waschmittel reinigen auch bei 30°C gründlich. Das spart gegenüber 60°C etwa 60% Energie.',
        potential_savings: '40-80€/Jahr',
        reduction: 12,
        implementation_time: 'Sofort',
        difficulty: 'easy',
        icon: 'fas fa-tint',
        color: '#06b6d4',
        steps: [
          'Waschmaschine auf 30°C einstellen',
          'Geeignetes Waschmittel verwenden',
          'Nur bei starker Verschmutzung höhere Temperaturen nutzen'
        ]
      },
      {
        id: 6,
        category: 'Smart Home',
        categoryId: 'smart',
        title: 'Smarte Thermostate installieren',
        description: 'Intelligente Heizungssteuerung passt die Temperatur automatisch an Ihre Anwesenheit an.',
        potential_savings: '150-300€/Jahr',
        reduction: 20,
        implementation_time: '2-4 Stunden',
        difficulty: 'medium',
        icon: 'fas fa-home',
        color: '#8b5cf6',
        steps: [
          'Kompatibles Smart Thermostat auswählen',
          'Installation durch Fachmann oder selbst',
          'App einrichten und konfigurieren',
          'Heizplan erstellen'
        ],
        tools: ['Smart Thermostat', 'Smartphone App', 'ggf. Elektriker']
      },
      {
        id: 7,
        category: 'Geräte',
        categoryId: 'appliances',
        title: 'Energieeffiziente Geräte nutzen',
        description: 'Beim Neukauf auf Energieeffizienzklasse A+++ achten. Alte Geräte sind oft Stromfresser.',
        potential_savings: '100-250€/Jahr',
        reduction: 25,
        implementation_time: 'Bei Neukauf',
        difficulty: 'medium',
        icon: 'fas fa-star',
        color: '#84cc16',
        steps: [
          'Verbrauch alter Geräte messen',
          'Energielabel bei Neukauf beachten',
          'Fördermöglichkeiten prüfen',
          'Alte Geräte fachgerecht entsorgen'
        ]
      },
      {
        id: 8,
        category: 'Heizen',
        categoryId: 'heating',
        title: 'Richtig lüften',
        description: 'Stoßlüften statt Dauerlüften: 5-10 Minuten bei weit geöffneten Fenstern tauscht die Luft aus ohne Wärmeverlust.',
        potential_savings: '80-150€/Jahr',
        reduction: 10,
        implementation_time: 'Sofort',
        difficulty: 'easy',
        icon: 'fas fa-wind',
        color: '#06b6d4',
        steps: [
          'Heizung vor dem Lüften ausschalten',
          'Fenster weit öffnen',
          '5-10 Minuten lüften',
          'Fenster schließen und heizen'
        ]
      }
    ])
    
    const filteredTips = computed(() => {
      if (selectedCategory.value === 'all') {
        return tips.value
      }
      return tips.value.filter(tip => tip.categoryId === selectedCategory.value)
    })
    
    const activeTips = computed(() => {
      return tips.value.filter(tip => activeTipIds.value.includes(tip.id))
    })
    
    const totalSavings = computed(() => {
      return activeTips.value.reduce((total, tip) => {
        return total + (tip.calculatedSavings || 0)
      }, 0)
    })
    
    const calculateSavings = () => {
      if (!calculator.value.annualKwh || !calculator.value.currentPrice) return
      
      tips.value.forEach(tip => {
        const annualCost = calculator.value.annualKwh * calculator.value.currentPrice
        const potentialSaving = (annualCost * tip.reduction) / 100
        tip.calculatedSavings = Math.round(potentialSaving)
      })
    }
    
    const toggleTip = (tipId) => {
      const index = activeTipIds.value.indexOf(tipId)
      if (index > -1) {
        activeTipIds.value.splice(index, 1)
      } else {
        activeTipIds.value.push(tipId)
      }
    }
    
    const getDifficultyText = (difficulty) => {
      switch (difficulty) {
        case 'easy': return 'Einfach'
        case 'medium': return 'Mittel'
        case 'hard': return 'Schwer'
        default: return 'Unbekannt'
      }
    }
    
    const loadTips = async () => {
      try {
        const response = await apiService.getUsageTips()
        if (response.data.tips) {
          // Merge API tips with local tips if needed
          console.log('Loaded tips from API:', response.data.tips)
        }
      } catch (error) {
        console.error('Error loading tips:', error)
        // Use local tips as fallback
      }
    }
    
    onMounted(() => {
      calculateSavings()
      loadTips()
    })
    
    return {
      calculator,
      selectedCategory,
      activeTipIds,
      categories,
      tips,
      filteredTips,
      activeTips,
      totalSavings,
      calculateSavings,
      toggleTip,
      getDifficultyText
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

.savings-calculator {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 16px;
  overflow: hidden;
}

.savings-calculator .card {
  background: transparent;
  border: none;
  box-shadow: none;
}

.savings-calculator .card-header {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.savings-calculator .card-title {
  color: white;
}

.calculator-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: start;
}

.calculator-form .form-label {
  color: rgba(255, 255, 255, 0.9);
}

.calculator-form .form-input {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.calculator-form .form-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.savings-result {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem;
  color: white;
}

.total-savings {
  text-align: center;
  margin-bottom: 1rem;
}

.savings-amount {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.savings-label {
  opacity: 0.9;
}

.savings-breakdown {
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 1rem;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.breakdown-name {
  opacity: 0.8;
}

.breakdown-amount {
  font-weight: 600;
}

.category-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.category-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  font-weight: 500;
  color: #6b7280;
}

.category-tab:hover {
  background: #f8fafc;
  border-color: #d1d5db;
}

.category-tab.active {
  background: #2563eb;
  border-color: #2563eb;
  color: white;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.tip-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.2s;
  position: relative;
}

.tip-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.tip-card.active {
  border-color: #10b981;
  box-shadow: 0 0 0 1px #10b981;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.tip-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.tip-meta {
  flex: 1;
}

.tip-category {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.9rem;
}

.tip-difficulty {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
  margin-top: 0.25rem;
}

.tip-difficulty.easy {
  background: #d1fae5;
  color: #065f46;
}

.tip-difficulty.medium {
  background: #fef3c7;
  color: #92400e;
}

.tip-difficulty.hard {
  background: #fef2f2;
  color: #b91c1c;
}

.tip-toggle {
  display: flex;
  align-items: center;
}

.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #d1d5db;
  transition: 0.2s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.2s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #10b981;
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.tip-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.tip-description {
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.tip-details {
  display: grid;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #374151;
}

.detail-item i {
  color: #6b7280;
  width: 16px;
}

.tip-steps, .tip-tools {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.tip-steps h4, .tip-tools h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.tip-steps ol, .tip-tools ul {
  padding-left: 1rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.tip-steps li, .tip-tools li {
  margin-bottom: 0.25rem;
}

.monitor-recommendation {
  border-radius: 16px;
  margin-top: 3rem;
}

.recommendation-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 3rem;
  align-items: center;
}

.recommendation-info h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1rem;
}

.recommendation-info p {
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.benefits-list {
  list-style: none;
}

.benefits-list li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  color: #374151;
}

.recommendation-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
}

.product-image {
  margin-bottom: 1rem;
}

.recommendation-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.price {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 0.5rem;
}

.savings-potential {
  color: #10b981;
  font-weight: 500;
  margin-bottom: 1rem;
}

.w-full {
  width: 100%;
}

@media (max-width: 1024px) {
  .calculator-grid {
    grid-template-columns: 1fr;
  }
  
  .recommendation-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}

@media (max-width: 768px) {
  .tips-grid {
    grid-template-columns: 1fr;
  }
  
  .category-tabs {
    flex-wrap: wrap;
  }
  
  .tip-header {
    flex-wrap: wrap;
    gap: 0.75rem;
  }
}
</style>
