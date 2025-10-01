<template>
  <div class="savings-tips py-8">
    <div class="container">
      <div class="page-header">
        <h1>Energie-Spartipps</h1>
        <p>Reduzieren Sie Ihren Stromverbrauch und sparen Sie Geld</p>
      </div>

    

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
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { apiService } from '../services/api'

export default {
  name: 'SavingsTips',
  setup() {
    const selectedCategory = ref('all')
    
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
      loadTips()
    })
    
    return {
      selectedCategory,
      categories,
      tips,
      filteredTips,
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

@media (max-width: 1024px) {
  .tips-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
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
