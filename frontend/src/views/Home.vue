<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1>Finden Sie den besten Stromtarif</h1>
          <p>Vergleichen Sie Energietarife und sparen Sie bis zu 500€ pro Jahr</p>
          
          <div class="hero-actions">
            <router-link to="/comparison" class="btn btn-primary btn-large">
              <i class="fas fa-calculator"></i>
              Jetzt vergleichen
            </router-link>
            <router-link to="/market" class="btn btn-secondary btn-large">
              <i class="fas fa-chart-line"></i>
              Marktdaten
            </router-link>
          </div>
          
          <div class="hero-stats">
            <div class="stat">
              <div class="stat-number">500€</div>
              <div class="stat-label">Durchschnittliche Ersparnis</div>
            </div>
            <div class="stat">
              <div class="stat-number">2 Min</div>
              <div class="stat-label">Zeit für Vergleich</div>
            </div>
            <div class="stat">
              <div class="stat-number">100%</div>
              <div class="stat-label">Kostenlos</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features py-16">
      <div class="container">
        <h2 class="text-center text-3xl font-bold mb-8">Warum EnergyCompare?</h2>
        <div class="grid grid-auto">
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-search"></i>
            </div>
            <h3>Einfacher Vergleich</h3>
            <p>Vergleichen Sie hunderte von Stromtarifen in wenigen Sekunden</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-euro-sign"></i>
            </div>
            <h3>Garantierte Ersparnis</h3>
            <p>Finden Sie den günstigsten Tarif und sparen Sie bares Geld</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-leaf"></i>
            </div>
            <h3>Ökostrom-Filter</h3>
            <p>Wählen Sie umweltfreundliche Tarife für eine grünere Zukunft</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">
              <i class="fas fa-shield-alt"></i>
            </div>
            <h3>100% Sicher</h3>
            <p>Ihre Daten sind bei uns sicher und werden nicht weitergegeben</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Quick Calculator -->
    <section class="quick-calc py-16 bg-gray-50">
      <div class="container">
        <div class="quick-calc-content">
          <div class="quick-calc-info">
            <h2>Schnellrechner</h2>
            <p>Ermitteln Sie in wenigen Sekunden Ihr Sparpotenzial</p>
            <ul class="benefits-list">
              <li><i class="fas fa-check text-green-600"></i> Aktueller Marktvergleich</li>
              <li><i class="fas fa-check text-green-600"></i> Alle Anbieter inklusive</li>
              <li><i class="fas fa-check text-green-600"></i> Keine versteckten Kosten</li>
              <li><i class="fas fa-check text-green-600"></i> Sofortige Ergebnisse</li>
            </ul>
          </div>
          
          <div class="quick-calc-form">
            <div class="card">
              <div class="card-header">
                <h3 class="card-title">
                  <i class="fas fa-calculator text-emerald-600"></i>
                  Ihr Sparpotenzial
                </h3>
              </div>
              
              <form @submit.prevent="calculateSavings">
                <div class="form-group">
                  <label class="form-label">Jahresverbrauch (kWh)</label>
                  <input 
                    type="number" 
                    v-model="quickCalc.annualKwh" 
                    class="form-input"
                    placeholder="z.B. 3500"
                    min="1000"
                    max="20000"
                    step="100"
                  >
                  <div class="form-help">
                    Durchschnitt: 1-Person: 2.000 kWh, 4-Personen: 4.500 kWh
                  </div>
                </div>
                
                <div class="form-group">
                  <label class="form-label">Aktuelle Jahreskosten (€)</label>
                  <input 
                    type="number" 
                    v-model="quickCalc.currentCost" 
                    class="form-input"
                    placeholder="z.B. 1200"
                    step="0.01"
                  >
                </div>
                
                <button type="submit" class="btn btn-primary w-full" :disabled="calculating">
                  <span v-if="calculating" class="loading-spinner small"></span>
                  <i v-else class="fas fa-calculator"></i>
                  {{ calculating ? 'Berechne...' : 'Sparpotenzial berechnen' }}
                </button>
                
                <div v-if="savingsResult" class="savings-result">
                  <div class="savings-amount">
                    <span class="amount">{{ savingsResult.savings }}€</span>
                    <span class="label">Jährliche Ersparnis möglich</span>
                  </div>
                  <router-link to="/comparison" class="btn btn-success w-full mt-4">
                    <i class="fas fa-arrow-right"></i>
                    Detaillierten Vergleich starten
                  </router-link>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-it-works py-16">
      <div class="container">
        <h2 class="text-center text-3xl font-bold mb-8">So funktioniert's</h2>
        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3>Verbrauch eingeben</h3>
              <p>Geben Sie Ihren Jahresverbrauch und Ihre Postleitzahl ein</p>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3>Tarife vergleichen</h3>
              <p>Wir zeigen Ihnen alle verfügbaren Tarife sortiert nach Preis</p>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3>Anbieter wechseln</h3>
              <p>Wählen Sie Ihren Wunschtarif und wechseln Sie direkt online</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Home',
  setup() {
    const quickCalc = ref({
      annualKwh: 3500,
      currentCost: null
    })
    
    const calculating = ref(false)
    const savingsResult = ref(null)
    
    const calculateSavings = async () => {
      if (!quickCalc.value.currentCost || !quickCalc.value.annualKwh) {
        return
      }
      
      calculating.value = true
      
      // Simulate calculation
      setTimeout(() => {
        const estimatedOptimalCost = quickCalc.value.annualKwh * 0.28 + (120 * 12)
        const savings = Math.max(0, quickCalc.value.currentCost - estimatedOptimalCost)
        
        savingsResult.value = {
          savings: Math.round(savings)
        }
        
        calculating.value = false
      }, 1000)
    }
    
    return {
      quickCalc,
      calculating,
      savingsResult,
      calculateSavings
    }
  }
}
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
  padding: 4rem 0;
  text-align: center;
}

.hero-content h1 {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.hero-content p {
  font-size: 1.25rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 3rem;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.stat {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.8;
}

.feature-card {
  text-align: center;
  padding: 2rem;
  border-radius: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: white;
  font-size: 1.5rem;
}

.feature-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.feature-card p {
  color: #6b7280;
  line-height: 1.6;
}

.quick-calc-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
}

.quick-calc-info h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #1f2937;
}

.quick-calc-info p {
  font-size: 1.1rem;
  color: #6b7280;
  margin-bottom: 2rem;
}

.benefits-list {
  list-style: none;
}

.benefits-list li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
  color: #374151;
}

.savings-result {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  margin-top: 1rem;
}

.savings-amount .amount {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: #059669;
}

.savings-amount .label {
  color: #065f46;
  font-size: 0.9rem;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.step-number {
  width: 48px;
  height: 48px;
  background: #059669;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.step-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.step-content p {
  color: #6b7280;
  line-height: 1.6;
}

.w-full {
  width: 100%;
}

@media (max-width: 768px) {
  .hero-content h1 {
    font-size: 2rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .hero-stats {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .quick-calc-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .steps {
    grid-template-columns: 1fr;
  }
}
</style>
