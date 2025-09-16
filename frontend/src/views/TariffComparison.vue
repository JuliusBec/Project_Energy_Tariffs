<template>
  <div class="tariff-comparison py-8">
    <div class="container">
      <div class="page-header">
        <h1>Dynamische Stromtarife Vergleich</h1>
        <p>Finden Sie den besten variablen Tarif für Ihren Bedarf</p>
        <div class="dynamic-info">
          <i class="fas fa-info-circle"></i>
          <span>Dynamische Tarife passen sich stündlich den Börsenpreisen an</span>
        </div>
      </div>

      <div class="comparison-grid">
        <!-- Calculator Form - Full Width -->
        <div class="calculator-section-full">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">
              <i class="fas fa-chart-line text-green-600"></i>
              Verbrauchsprofil für dynamische Tarife
            </h2>
            <p class="card-subtitle">
              Optimieren Sie Ihre Ersparnisse durch intelligentes Lastmanagement
            </p>
          </div>

            <form @submit.prevent="calculateTariffs">
              <!-- Smart Meter Selection -->
              <div class="form-group">
                <label class="form-label">Verfügen Sie über einen Smart Meter?</label>
                <div class="meter-selection">
                  <label class="meter-option" :class="{ active: formData.hasSmartMeter }">
                    <input type="radio" v-model="formData.hasSmartMeter" :value="true">
                    <div class="meter-card">
                      <i class="fas fa-wifi"></i>
                      <h4>Smart Meter vorhanden</h4>
                      <p>Ich kann meine Verbrauchsdaten hochladen</p>
                      <div class="meter-benefits">
                        <span><i class="fas fa-check"></i> Präzise Analyse</span>
                        <span><i class="fas fa-check"></i> Optimale Tarife</span>
                      </div>
                    </div>
                  </label>
                  
                  <label class="meter-option" :class="{ active: !formData.hasSmartMeter }">
                    <input type="radio" v-model="formData.hasSmartMeter" :value="false">
                    <div class="meter-card">
                      <i class="fas fa-calculator"></i>
                      <h4>Kein Smart Meter</h4>
                      <p>Ich gebe meine Daten manuell ein</p>
                      <div class="meter-benefits">
                        <span><i class="fas fa-check"></i> Einfach</span>
                        <span><i class="fas fa-check"></i> Schnell</span>
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Smart Meter Section -->
              <div v-if="formData.hasSmartMeter" class="smart-meter-section">
                <div class="section-header">
                  <i class="fas fa-upload"></i>
                  <h3>Smart Meter Daten hochladen</h3>
                  <p>Laden Sie Ihre Verbrauchsdaten für eine präzise Analyse hoch</p>
                </div>

                <div class="form-group">
                  <label class="form-label">Verbrauchsdaten hochladen *</label>
                  <div class="upload-section">
                    <div class="upload-area" :class="{ 'dragover': isDragOver, 'has-file': uploadedFile }" 
                         @drop="handleFileDrop" 
                         @dragover.prevent="isDragOver = true" 
                         @dragleave="isDragOver = false">
                      <input 
                        type="file" 
                        ref="fileInput" 
                        @change="handleFileSelect" 
                        accept=".csv,.xlsx,.xls"
                        style="display: none"
                      >
                      
                      <div v-if="!uploadedFile" class="upload-placeholder">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>CSV-Datei hier ablegen oder 
                          <button type="button" @click="$refs.fileInput.click()" class="upload-link">
                            durchsuchen
                          </button>
                        </p>
                        <div class="upload-hint">
                          Unterstützte Formate: CSV, Excel (.xlsx, .xls)
                        </div>
                      </div>
                      
                      <div v-else class="file-info">
                        <div class="file-details">
                          <i class="fas fa-file-csv"></i>
                          <div>
                            <div class="file-name">{{ uploadedFile.name }}</div>
                            <div class="file-size">{{ formatFileSize(uploadedFile.size) }}</div>
                            <div v-if="csvData" class="file-preview">
                              {{ csvData.length }} Datensätze erkannt
                              <span v-if="formData.annualKwh"> | {{ formData.annualKwh }} kWh/Jahr</span>
                            </div>
                          </div>
                        </div>
                        <button type="button" @click="removeFile" class="remove-file">
                          <i class="fas fa-times"></i>
                        </button>
                      </div>
                    </div>
                    
                    <div v-if="fileError" class="file-error">
                      <i class="fas fa-exclamation-triangle"></i>
                      {{ fileError }}
                    </div>
                    
                    <div class="form-help">
                      Upload Ihrer stündlichen/täglichen Verbrauchsdaten für präzisere Tarifempfehlungen. 
                      <br>Erwartetes Format: Datum, Uhrzeit, Verbrauch (kWh)
                    </div>
                  </div>
                </div>
              </div>

              <!-- Manual Input Section -->
              <div v-else class="manual-input-section">
                <div class="section-header">
                  <i class="fas fa-edit"></i>
                  <h3>Verbrauchsdaten eingeben</h3>
                  <p>Geben Sie Ihre Verbrauchsinformationen manuell ein</p>
                </div>

                <div class="form-group">
                  <label class="form-label">Jahresverbrauch (kWh) *</label>
                  <input 
                    type="number" 
                    v-model="formData.annualKwh" 
                    class="form-input"
                    placeholder="z.B. 3500"
                    min="1000"
                    max="20000"
                    step="100"
                    required
                  >
                  <div class="form-help">
                    Durchschnittswerte: 1-Person: 2.000 kWh | 2-Personen: 3.500 kWh | 4-Personen: 4.500 kWh
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Haushaltstyp</label>
                  <select v-model="formData.householdType" class="form-select" @change="updateConsumptionFromHousehold">
                    <option value="">Bitte wählen</option>
                    <option value="single">1-Person Haushalt</option>
                    <option value="couple">2-Personen Haushalt</option>
                    <option value="family-small">3-Personen Haushalt</option>
                    <option value="family-large">4+ Personen Haushalt</option>
                  </select>
                  <div class="form-help">
                    Automatische Schätzung des Jahresverbrauchs basierend auf Ihrem Haushaltstyp
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Hauptverbrauchszeiten</label>
                  <div class="time-grid">
                    <label class="time-option">
                      <input type="checkbox" v-model="formData.morningUsage">
                      <span class="time-card">
                        <i class="fas fa-sun"></i>
                        <div>Morgens (6-10 Uhr)</div>
                      </span>
                    </label>
                    <label class="time-option">
                      <input type="checkbox" v-model="formData.dayUsage">
                      <span class="time-card">
                        <i class="fas fa-sun"></i>
                        <div>Tags (10-18 Uhr)</div>
                      </span>
                    </label>
                    <label class="time-option">
                      <input type="checkbox" v-model="formData.eveningUsage">
                      <span class="time-card">
                        <i class="fas fa-moon"></i>
                        <div>Abends (18-22 Uhr)</div>
                      </span>
                    </label>
                    <label class="time-option">
                      <input type="checkbox" v-model="formData.nightUsage">
                      <span class="time-card">
                        <i class="fas fa-moon"></i>
                        <div>Nachts (22-6 Uhr)</div>
                      </span>
                    </label>
                  </div>
                  <div class="form-help">
                    Wählen Sie die Zeiten aus, in denen Sie hauptsächlich Strom verbrauchen
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Hauptverbraucher im Haushalt</label>
                  <div class="appliances-grid">
                    <label class="appliance-option">
                      <input type="checkbox" v-model="formData.hasElectricHeating">
                      <span class="appliance-card">
                        <i class="fas fa-thermometer-half"></i>
                        <div>Elektroheizung</div>
                      </span>
                    </label>
                    <label class="appliance-option">
                      <input type="checkbox" v-model="formData.hasHeatPump">
                      <span class="appliance-card">
                        <i class="fas fa-wind"></i>
                        <div>Wärmepumpe</div>
                      </span>
                    </label>
                    <label class="appliance-option">
                      <input type="checkbox" v-model="formData.hasElectricCar">
                      <span class="appliance-card">
                        <i class="fas fa-car"></i>
                        <div>E-Auto</div>
                      </span>
                    </label>
                    <label class="appliance-option">
                      <input type="checkbox" v-model="formData.hasSauna">
                      <span class="appliance-card">
                        <i class="fas fa-hot-tub"></i>
                        <div>Sauna</div>
                      </span>
                    </label>
                    <label class="appliance-option">
                      <input type="checkbox" v-model="formData.hasPool">
                      <span class="appliance-card">
                        <i class="fas fa-swimmer"></i>
                        <div>Pool/Pumpe</div>
                      </span>
                    </label>
                    <label class="appliance-option">
                      <input type="checkbox" v-model="formData.hasAirConditioning">
                      <span class="appliance-card">
                        <i class="fas fa-snowflake"></i>
                        <div>Klimaanlage</div>
                      </span>
                    </label>
                  </div>
                  <div class="form-help">
                    Große Verbraucher beeinflussen Ihren Stromverbrauch und die Tarifempfehlung
                  </div>
                </div>
              </div>

              <!-- Common fields for manual input only -->
              <div v-if="!formData.hasSmartMeter">
                <div class="form-group">
                  <label class="form-label">Flexibilität Ihres Verbrauchs</label>
                  <select v-model="formData.flexibility" class="form-select">
                    <option value="low">Niedrig - Fester Tagesablauf</option>
                    <option value="medium">Mittel - Teilweise flexibel</option>
                    <option value="high">Hoch - Sehr flexibel</option>
                  </select>
                  <div class="form-help">
                    Höhere Flexibilität = größere Ersparnisse bei dynamischen Tarifen
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Smart Home Ausstattung</label>
                  <select v-model="formData.smartHome" class="form-select">
                    <option value="none">Keine Smart Home Geräte</option>
                    <option value="basic">Grundausstattung (Smart Thermostat, etc.)</option>
                    <option value="advanced">Erweitert (Home Energy Management)</option>
                  </select>
                  <div class="form-help">
                    Smart Home hilft bei der automatischen Optimierung des Verbrauchs
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Postleitzahl</label>
                  <input 
                    type="text" 
                    v-model="formData.zipCode" 
                    class="form-input"
                    placeholder="z.B. 80331"
                    pattern="[0-9]{5}"
                    maxlength="5"
                  >
                  <div class="form-help">
                    Für regionale Tarifverfügbarkeit (optional)
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Aktueller Anbieter (optional)</label>
                  <input 
                    type="text" 
                    v-model="formData.currentProvider" 
                    class="form-input"
                    placeholder="z.B. Stadtwerke München"
                  >
                </div>

                <div class="form-group">
                  <label class="form-label">Aktuelle Jahreskosten (€)</label>
                  <input 
                    type="number" 
                    v-model="formData.currentCost" 
                    class="form-input"
                    placeholder="z.B. 1200"
                    step="0.01"
                    min="0"
                  >
                  <div class="form-help">
                    Für Ersparnis-Berechnung (optional)
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Bevorzugte Verbrauchszeiten</label>
                  <div class="checkbox-group">
                    <label class="form-checkbox">
                      <input type="checkbox" v-model="formData.nightUsage">
                      <span>Hoher Nachtverbrauch (22:00 - 6:00)</span>
                    </label>
                  </div>
                  <div class="checkbox-group">
                    <label class="form-checkbox">
                      <input type="checkbox" v-model="formData.weekendUsage">
                      <span>Hoher Wochenendverbrauch</span>
                    </label>
                  </div>
                  <div class="form-help">
                    Diese Zeiten haben oft niedrigere Börsenpreise
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Preisvolatilität-Toleranz</label>
                  <select v-model="formData.volatilityTolerance" class="form-select">
                    <option value="low">Niedrig - Stabilere Preise bevorzugt</option>
                    <option value="medium">Mittel - Moderate Schwankungen OK</option>
                    <option value="high">Hoch - Maximale Ersparnisse trotz Schwankungen</option>
                  </select>
                  <div class="form-help">
                    Dynamische Tarife schwanken täglich - wählen Sie Ihre Risikobereitschaft
                  </div>
                </div>

                <div class="checkbox-group">
                  <label class="form-checkbox">
                    <input type="checkbox" v-model="formData.onlyDynamic">
                    <span>Nur echte dynamische Tarife (stündliche Preisanpassung)</span>
                  </label>
                </div>

                <div class="checkbox-group">
                  <label class="form-checkbox">
                    <input type="checkbox" v-model="formData.appIntegration">
                    <span>App-Integration für Preisbenachrichtigungen erforderlich</span>
                  </label>
                </div>
              </div>

              <button type="submit" class="btn btn-primary w-full" :disabled="loading">
                <span v-if="loading" class="loading-spinner small"></span>
                <i v-else class="fas fa-chart-line"></i>
                {{ loading ? 'Analysiere Tarife...' : 'Dynamische Tarife finden' }}
              </button>
            </form>
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div class="results-section">
        <!-- Loading State -->
          <div v-if="loading" class="loading">
            <div class="loading-spinner"></div>
            <p>Tarife werden berechnet...</p>
          </div>

          <!-- Results -->
          <div v-else-if="results.length > 0" class="results">
            <div class="results-header">
              <h3>{{ results.length }} Tarife gefunden</h3>
              <p class="results-summary">
                Für {{ formData.annualKwh }} kWh Jahresverbrauch
                <span v-if="formData.currentCost"> | Aktuelle Kosten: {{ formData.currentCost }}€</span>
              </p>
              
              <div class="sort-controls">
                <label>Sortieren nach:</label>
                <select v-model="sortBy" @change="sortResults" class="form-select">
                  <option value="annual_cost">Gesamtkosten (niedrig → hoch)</option>
                  <option value="kwh_price">kWh-Preis (niedrig → hoch)</option>
                  <option value="base_price">Grundpreis (niedrig → hoch)</option>
                  <option value="green_energy">Ökostrom zuerst</option>
                </select>
              </div>
            </div>

            <div class="tariff-list">
              <div 
                v-for="(tariff, index) in sortedResults" 
                :key="tariff.id"
                class="tariff-card"
                :class="{ 'recommended': index === 0 }"
              >
                <div class="tariff-rank" v-if="index < 3">
                  {{ index + 1 }}
                </div>

                <div class="tariff-header">
                  <div class="tariff-info">
                    <h4 class="tariff-name">{{ tariff.name }}</h4>
                    <p class="tariff-description">{{ tariff.description }}</p>
                    
                    <div class="tariff-badges">
                      <span v-if="tariff.is_dynamic" class="badge badge-dynamic">
                        <i class="fas fa-chart-line"></i>
                        Dynamisch
                      </span>
                      <span v-if="tariff.green_energy" class="badge badge-green">
                        <i class="fas fa-leaf"></i>
                        Ökostrom
                      </span>
                      <span v-if="tariff.app_available" class="badge badge-tech">
                        <i class="fas fa-mobile-alt"></i>
                        App
                      </span>
                      <span v-if="tariff.automation_ready" class="badge badge-smart">
                        <i class="fas fa-home"></i>
                        Smart Ready
                      </span>
                      <span v-if="index === 0" class="badge badge-gold">
                        <i class="fas fa-star"></i>
                        Empfohlen
                      </span>
                    </div>
                  </div>

                  <div class="tariff-price">
                    <div class="annual-cost">{{ tariff.annual_cost }}€</div>
                    <div class="monthly-cost">{{ tariff.monthly_cost }}€/Monat</div>
                  </div>
                </div>

                <div class="tariff-details">
                  <div class="price-model-info" v-if="tariff.price_model">
                    <h4><i class="fas fa-chart-area"></i> Preismodell</h4>
                    <p>{{ tariff.price_model }}</p>
                  </div>
                  
                  <div class="detail-grid">
                    <div class="detail-item">
                      <i class="fas fa-euro-sign"></i>
                      <span>Grundpreis: {{ tariff.base_price }}€/Monat</span>
                    </div>
                    <div class="detail-item">
                      <i class="fas fa-bolt"></i>
                      <span>Aufschlag: {{ tariff.kwh_price }}€/kWh</span>
                    </div>
                    <div class="detail-item">
                      <i class="fas fa-calendar"></i>
                      <span>Laufzeit: {{ tariff.contract_duration }} Monate</span>
                    </div>
                    <div class="detail-item" v-if="tariff.volatility">
                      <i class="fas fa-wave-square"></i>
                      <span>Volatilität: {{ tariff.volatility }}</span>
                    </div>
                    <div class="detail-item" v-if="tariff.avg_savings">
                      <i class="fas fa-piggy-bank"></i>
                      <span>Ø Ersparnis: {{ tariff.avg_savings }}</span>
                    </div>
                    <div class="detail-item" v-if="tariff.optimization_score">
                      <i class="fas fa-percentage"></i>
                      <span>Ihr Optimierungspotenzial: {{ tariff.optimization_score }}%</span>
                    </div>
                  </div>
                  
                  <div v-if="tariff.is_dynamic" class="dynamic-features">
                    <h4><i class="fas fa-cogs"></i> Dynamische Features</h4>
                    <ul>
                      <li v-if="tariff.price_forecast">
                        <i class="fas fa-check text-green-600"></i>
                        Preisvorhersage verfügbar
                      </li>
                      <li v-if="tariff.app_available">
                        <i class="fas fa-check text-green-600"></i>
                        Mobile App mit Push-Benachrichtigungen
                      </li>
                      <li v-if="tariff.automation_ready">
                        <i class="fas fa-check text-green-600"></i>
                        Smart Home Integration
                      </li>
                      <li v-else>
                        <i class="fas fa-times text-red-600"></i>
                        Keine Smart Home Integration
                      </li>
                    </ul>
                  </div>
                </div>

                <div v-if="tariff.potential_savings > 0" class="optimization-savings">
                  <i class="fas fa-chart-line"></i>
                  Durch intelligente Verbrauchssteuerung sparen Sie zusätzlich {{ tariff.potential_savings }}€ pro Jahr!
                </div>

                <div v-if="formData.currentCost && tariff.savings_vs_current > 0" class="savings">
                  <i class="fas fa-piggy-bank"></i>
                  Sie sparen {{ tariff.savings_vs_current }}€ pro Jahr gegenüber Ihrem aktuellen Tarif!
                </div>

                <div class="tariff-actions">
                  <button class="btn btn-primary" @click="selectTariff(tariff)">
                    <i class="fas fa-check"></i>
                    Tarif wählen
                  </button>
                  <button class="btn btn-secondary" @click="showTariffDetails(tariff)">
                    <i class="fas fa-info-circle"></i>
                    Details
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- No Results -->
          <div v-else-if="!loading && searchPerformed" class="no-results">
            <div class="no-results-content">
              <i class="fas fa-search"></i>
              <h3>Keine Tarife gefunden</h3>
              <p>Versuchen Sie andere Suchkriterien oder erhöhen Sie den maximalen kWh-Preis.</p>
            </div>
          </div>

      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { apiService } from '../services/api'

export default {
  name: 'TariffComparison',
  setup() {
    const formData = ref({
      hasSmartMeter: false,
      annualKwh: 3500,
      zipCode: '',
      currentProvider: '',
      currentCost: null,
      flexibility: 'medium',
      smartHome: 'none',
      nightUsage: false,
      weekendUsage: false,
      volatilityTolerance: 'medium',
      onlyDynamic: true,
      appIntegration: false,
      // Manual input fields
      householdType: '',
      morningUsage: false,
      dayUsage: false,
      eveningUsage: false,
      hasElectricHeating: false,
      hasHeatPump: false,
      hasElectricCar: false,
      hasSauna: false,
      hasPool: false,
      hasAirConditioning: false
    })
    
    const loading = ref(false)
    const results = ref([])
    const searchPerformed = ref(false)
    const sortBy = ref('annual_cost')
    
    // File upload functionality
    const uploadedFile = ref(null)
    const csvData = ref(null)
    const fileError = ref('')
    const isDragOver = ref(false)
    
    const sortedResults = computed(() => {
      const sorted = [...results.value]
      
      switch (sortBy.value) {
        case 'annual_cost':
          return sorted.sort((a, b) => a.annual_cost - b.annual_cost)
        case 'kwh_price':
          return sorted.sort((a, b) => a.kwh_price - b.kwh_price)
        case 'base_price':
          return sorted.sort((a, b) => a.base_price - b.base_price)
        case 'green_energy':
          return sorted.sort((a, b) => {
            if (a.green_energy && !b.green_energy) return -1
            if (!a.green_energy && b.green_energy) return 1
            return a.annual_cost - b.annual_cost
          })
        default:
          return sorted
      }
    })
    
    const calculateTariffs = async () => {
      loading.value = true
      searchPerformed.value = true
      
      try {
        const response = await apiService.calculateTariffs({
          annual_kwh: formData.value.annualKwh,
          zip_code: formData.value.zipCode,
          green_only: formData.value.greenEnergyOnly,
          max_price: formData.value.maxPrice,
          short_term_only: formData.value.shortTermOnly
        })
        
        results.value = response.data.results.map(tariff => ({
          ...tariff,
          savings_vs_current: formData.value.currentCost ? 
            Math.max(0, formData.value.currentCost - tariff.annual_cost) : 0
        }))
        
        // Filter by contract duration if needed
        if (formData.value.shortTermOnly) {
          results.value = results.value.filter(t => t.contract_duration <= 12)
        }
        
      } catch (error) {
        console.error('Error calculating tariffs:', error)
        // Generate mock data if API fails
        generateMockTariffs()
      } finally {
        loading.value = false
      }
    }
    
    const generateMockTariffs = () => {
      const mockTariffs = [
        {
          id: 1,
          name: "aWATTar HOURLY",
          base_price: 8.90,
          kwh_price: 0.245,
          is_dynamic: true,
          price_model: "Stündliche Börsenpreise + 0.245€/kWh",
          green_energy: true,
          contract_duration: 12,
          description: "Echter dynamischer Tarif mit stündlicher Abrechnung nach Börsenpreis",
          app_available: true,
          price_forecast: true,
          automation_ready: true,
          avg_savings: "15-25%",
          volatility: "hoch"
        },
        {
          id: 2,
          name: "Tibber Dynamic",
          base_price: 9.90,
          kwh_price: 0.235,
          is_dynamic: true,
          price_model: "Börsenpreis + 0.235€/kWh + 9.90€/Monat",
          green_energy: true,
          contract_duration: 12,
          description: "Intelligenter Tarif mit KI-basierter Verbrauchsoptimierung",
          app_available: true,
          price_forecast: true,
          automation_ready: true,
          avg_savings: "20-30%",
          volatility: "mittel-hoch"
        },
        {
          id: 3,
          name: "Energy2market Flex",
          base_price: 12.50,
          kwh_price: 0.220,
          is_dynamic: true,
          price_model: "Day-Ahead Preise + 0.220€/kWh",
          green_energy: false,
          contract_duration: 12,
          description: "Professioneller dynamischer Tarif für optimierte Haushalte",
          app_available: true,
          price_forecast: true,
          automation_ready: true,
          avg_savings: "18-28%",
          volatility: "hoch"
        },
        {
          id: 4,
          name: "Octopus Energy Agile",
          base_price: 11.90,
          kwh_price: 0.255,
          is_dynamic: true,
          price_model: "30-min Intervalle basierend auf Börsenpreisen",
          green_energy: true,
          contract_duration: 12,
          description: "Halbstündliche Preisanpassung mit grüner Energie",
          app_available: true,
          price_forecast: true,
          automation_ready: false,
          avg_savings: "12-22%",
          volatility: "sehr hoch"
        },
        {
          id: 5,
          name: "ENTEGA Vario Smart",
          base_price: 15.90,
          kwh_price: 0.275,
          is_dynamic: false,
          price_model: "Variable Preise mit Preisgarantie-Puffern",
          green_energy: true,
          contract_duration: 24,
          description: "Halb-dynamischer Tarif mit Preisschutz nach oben",
          app_available: false,
          price_forecast: false,
          automation_ready: false,
          avg_savings: "5-15%",
          volatility: "niedrig-mittel"
        }
      ]
      
      // Filter based on user preferences
      let filteredTariffs = mockTariffs
      
      if (formData.value.onlyDynamic) {
        filteredTariffs = filteredTariffs.filter(t => t.is_dynamic)
      }
      
      if (formData.value.appIntegration) {
        filteredTariffs = filteredTariffs.filter(t => t.app_available)
      }
      
      // Calculate costs and add optimization potential based on flexibility
      results.value = filteredTariffs.map(tariff => {
        const baseAnnualCost = (tariff.base_price * 12) + (formData.value.annualKwh * tariff.kwh_price)
        
        // Calculate dynamic savings based on user profile
        let dynamicSavingsFactor = 1.0
        
        if (tariff.is_dynamic) {
          // Flexibility bonus
          if (formData.value.flexibility === 'high') dynamicSavingsFactor *= 0.85
          else if (formData.value.flexibility === 'medium') dynamicSavingsFactor *= 0.92
          
          // Smart home bonus
          if (formData.value.smartHome === 'advanced') dynamicSavingsFactor *= 0.90
          else if (formData.value.smartHome === 'basic') dynamicSavingsFactor *= 0.95
          
          // Night usage bonus
          if (formData.value.nightUsage) dynamicSavingsFactor *= 0.93
          
          // Weekend usage bonus  
          if (formData.value.weekendUsage) dynamicSavingsFactor *= 0.97
        }
        
        const optimizedAnnualCost = baseAnnualCost * dynamicSavingsFactor
        const monthly_cost = optimizedAnnualCost / 12
        
        return {
          ...tariff,
          annual_cost: Math.round(optimizedAnnualCost * 100) / 100,
          base_annual_cost: Math.round(baseAnnualCost * 100) / 100,
          monthly_cost: Math.round(monthly_cost * 100) / 100,
          potential_savings: Math.round((baseAnnualCost - optimizedAnnualCost) * 100) / 100,
          savings_vs_current: formData.value.currentCost ? 
            Math.max(0, formData.value.currentCost - optimizedAnnualCost) : 0,
          optimization_score: Math.round((1 - dynamicSavingsFactor) * 100)
        }
      })
    }
    
    const sortResults = () => {
      // Trigger reactivity by updating the computed property
    }
    
    const selectTariff = (tariff) => {
      alert(`Sie haben den Tarif "${tariff.name}" ausgewählt. In einer echten Anwendung würden Sie jetzt zum Wechselprozess weitergeleitet.`)
    }
    
    const showTariffDetails = (tariff) => {
      alert(`Tariff Details für "${tariff.name}":\n\nGrundpreis: ${tariff.base_price}€/Monat\nArbeitspreis: ${tariff.kwh_price}€/kWh\nLaufzeit: ${tariff.contract_duration} Monate\nÖkostrom: ${tariff.green_energy ? 'Ja' : 'Nein'}\n\n${tariff.description}`)
    }
    
    // File upload functions
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        processFile(file)
      }
    }
    
    const handleFileDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      
      const file = event.dataTransfer.files[0]
      if (file) {
        processFile(file)
      }
    }
    
    const processFile = async (file) => {
      fileError.value = ''
      
      // Validate file type
      const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
      const allowedExtensions = ['.csv', '.xlsx', '.xls']
      
      const hasValidType = allowedTypes.includes(file.type) || 
                          allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
      
      if (!hasValidType) {
        fileError.value = 'Bitte wählen Sie eine CSV- oder Excel-Datei (.csv, .xlsx, .xls)'
        return
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        fileError.value = 'Die Datei ist zu groß. Maximale Größe: 5MB'
        return
      }
      
      uploadedFile.value = file
      
      try {
        if (file.name.toLowerCase().endsWith('.csv')) {
          await parseCSV(file)
        } else {
          fileError.value = 'Excel-Dateien werden noch nicht unterstützt. Bitte verwenden Sie CSV-Format.'
          uploadedFile.value = null
        }
      } catch (error) {
        console.error('Error parsing file:', error)
        fileError.value = 'Fehler beim Verarbeiten der Datei. Bitte überprüfen Sie das Format.'
        uploadedFile.value = null
      }
    }
    
    const parseCSV = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        
        reader.onload = (e) => {
          try {
            const text = e.target.result
            const lines = text.split('\n')
            const data = []
            
            // Skip header row and parse data
            for (let i = 1; i < lines.length; i++) {
              const line = lines[i].trim()
              if (line) {
                const columns = line.split(',')
                if (columns.length >= 3) {
                  data.push({
                    date: columns[0],
                    time: columns[1],
                    consumption: parseFloat(columns[2])
                  })
                }
              }
            }
            
            if (data.length === 0) {
              fileError.value = 'Keine gültigen Daten in der CSV-Datei gefunden'
              uploadedFile.value = null
              reject(new Error('No valid data found'))
              return
            }
            
            csvData.value = data
            
            // Calculate annual consumption from CSV data
            const totalConsumption = data.reduce((sum, row) => sum + (row.consumption || 0), 0)
            if (totalConsumption > 0) {
              formData.value.annualKwh = Math.round(totalConsumption)
            }
            
            resolve(data)
          } catch (error) {
            reject(error)
          }
        }
        
        reader.onerror = () => reject(new Error('File reading error'))
        reader.readAsText(file)
      })
    }
    
    const removeFile = () => {
      uploadedFile.value = null
      csvData.value = null
      fileError.value = ''
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const updateConsumptionFromHousehold = () => {
      const consumptionMap = {
        'single': 2000,
        'couple': 3500,
        'family-small': 4500,
        'family-large': 5500
      }
      
      if (formData.value.householdType && consumptionMap[formData.value.householdType]) {
        formData.value.annualKwh = consumptionMap[formData.value.householdType]
      }
    }
    
    // Load URL parameters if any
    onMounted(() => {
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.get('kwh')) {
        formData.value.annualKwh = parseInt(urlParams.get('kwh'))
        calculateTariffs()
      }
    })
    
    return {
      formData,
      loading,
      results,
      searchPerformed,
      sortBy,
      sortedResults,
      uploadedFile,
      csvData,
      fileError,
      isDragOver,
      calculateTariffs,
      sortResults,
      selectTariff,
      showTariffDetails,
      handleFileSelect,
      handleFileDrop,
      removeFile,
      formatFileSize,
      updateConsumptionFromHousehold
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
  margin-bottom: 1rem;
}

.dynamic-info {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #f0fdf4;
  color: #15803d;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  border: 1px solid #bbf7d0;
}

.comparison-grid {
  display: flex;
  flex-direction: column;
  gap: 3rem;
  align-items: center;
}

.calculator-section-full {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.results-section {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
}

.checkbox-group {
  margin-bottom: 1rem;
}

.checkbox-group:last-of-type {
  margin-bottom: 2rem;
}

.results-header {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  border: 1px solid #e5e7eb;
}

.results-header h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.results-summary {
  color: #6b7280;
  margin-bottom: 1rem;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sort-controls label {
  font-weight: 500;
  color: #374151;
}

.sort-controls select {
  min-width: 250px;
}

.tariff-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tariff-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  position: relative;
  transition: all 0.2s;
}

.tariff-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.tariff-card.recommended {
  border-color: #10b981;
  box-shadow: 0 0 0 1px #10b981;
}

.tariff-rank {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 32px;
  height: 32px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
}

.tariff-rank:nth-child(2) {
  background: #f59e0b;
}

.tariff-rank:nth-child(3) {
  background: #ef4444;
}

.tariff-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.tariff-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.tariff-description {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.tariff-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.badge-green {
  background: #d1fae5;
  color: #065f46;
}

.badge-blue {
  background: #dbeafe;
  color: #1e40af;
}

.badge-gold {
  background: #fef3c7;
  color: #92400e;
}

.tariff-price {
  text-align: right;
}

.annual-cost {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.monthly-cost {
  color: #6b7280;
  font-size: 0.9rem;
}

.tariff-details {
  margin: 1rem 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
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

.savings {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
  padding: 0.75rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tariff-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.tariff-actions .btn {
  flex: 1;
}

.no-results, .initial-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.no-results-content, .initial-content {
  max-width: 400px;
  margin: 0 auto;
}

.no-results i, .initial-content i {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: block;
  color: #d1d5db;
}

.no-results h3, .initial-content h3 {
  font-size: 1.5rem;
  color: #374151;
  margin-bottom: 1rem;
}

.benefits {
  list-style: none;
  text-align: left;
  margin-top: 1.5rem;
}

.benefits li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #374151;
}

.benefits i {
  color: #10b981;
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

.w-full {
  width: 100%;
}

/* File Upload Styles */
.upload-section {
  margin-top: 0.5rem;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
  transition: all 0.2s;
  cursor: pointer;
}

.upload-area:hover,
.upload-area.dragover {
  border-color: #059669;
  background: #f0fdf4;
}

.upload-area.has-file {
  border-style: solid;
  border-color: #059669;
  background: #f0fdf4;
}

.upload-placeholder i {
  font-size: 2rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.upload-placeholder p {
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.upload-link {
  color: #059669;
  text-decoration: underline;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
}

.upload-link:hover {
  color: #047857;
}

.upload-hint {
  font-size: 0.8rem;
  color: #9ca3af;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-details i {
  font-size: 1.5rem;
  color: #059669;
}

.file-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.file-size {
  font-size: 0.8rem;
  color: #6b7280;
}

.file-preview {
  font-size: 0.8rem;
  color: #059669;
  font-weight: 500;
}

.remove-file {
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #dc2626;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-file:hover {
  background: #fecaca;
  border-color: #f87171;
}

.file-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #dc2626;
  background: #fee2e2;
  border: 1px solid #fecaca;
  padding: 0.75rem;
  border-radius: 6px;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.file-error i {
  color: #dc2626;
}

/* Smart Meter Selection Styles */
.meter-selection {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

.meter-option {
  cursor: pointer;
}

.meter-option input[type="radio"] {
  display: none;
}

.meter-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.2s;
  background: white;
}

.meter-option.active .meter-card {
  border-color: #059669;
  background: #f0fdf4;
}

.meter-card i {
  font-size: 2rem;
  color: #059669;
  margin-bottom: 1rem;
}

.meter-card h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.meter-card p {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.meter-benefits {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.meter-benefits span {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #059669;
}

.meter-benefits i {
  font-size: 0.7rem;
}

/* Section Headers */
.section-header {
  text-align: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.section-header i {
  font-size: 2rem;
  color: #059669;
  margin-bottom: 0.5rem;
}

.section-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.section-header p {
  color: #6b7280;
  font-size: 0.9rem;
}

/* Time Selection Grid */
.time-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.time-option {
  cursor: pointer;
}

.time-option input[type="checkbox"] {
  display: none;
}

.time-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  transition: all 0.2s;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.time-option input:checked + .time-card {
  border-color: #059669;
  background: #f0fdf4;
  color: #059669;
}

.time-card i {
  font-size: 1.2rem;
  color: #6b7280;
}

.time-option input:checked + .time-card i {
  color: #059669;
}

.time-card div {
  font-size: 0.9rem;
  font-weight: 500;
}

/* Appliances Grid */
.appliances-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.appliance-option {
  cursor: pointer;
}

.appliance-option input[type="checkbox"] {
  display: none;
}

.appliance-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  transition: all 0.2s;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-height: 80px;
  justify-content: center;
}

.appliance-option input:checked + .appliance-card {
  border-color: #059669;
  background: #f0fdf4;
  color: #059669;
}

.appliance-card i {
  font-size: 1.2rem;
  color: #6b7280;
}

.appliance-option input:checked + .appliance-card i {
  color: #059669;
}

.appliance-card div {
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
}

@media (max-width: 1024px) {
  .calculator-section-full {
    max-width: 100%;
    padding: 0 1rem;
  }
  
  .results-section {
    max-width: 100%;
    padding: 0 1rem;
  }
}

@media (max-width: 768px) {
  .tariff-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .tariff-price {
    text-align: left;
    margin-top: 0.5rem;
  }
  
  .tariff-rank {
    position: static;
    margin-bottom: 1rem;
    align-self: flex-start;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .tariff-actions {
    flex-direction: column;
  }
  
  .sort-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .sort-controls select {
    min-width: 100%;
  }
}

/* Dynamic tariff specific styles */
.card-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.badge-dynamic {
  background: #dbeafe;
  color: #1e40af;
}

.badge-tech {
  background: #ede9fe;
  color: #7c3aed;
}

.badge-smart {
  background: #fef3c7;
  color: #92400e;
}

.price-model-info {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.price-model-info h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.price-model-info p {
  color: #6b7280;
  font-size: 0.85rem;
  margin: 0;
}

.dynamic-features {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.dynamic-features h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #15803d;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dynamic-features ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.dynamic-features li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: #374151;
}

.optimization-savings {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
  padding: 0.75rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
