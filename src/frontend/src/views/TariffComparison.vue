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
                <label class="form-label">Verfügen Sie über einen Smart Meter? *</label>
                <div class="meter-selection">
                  <label class="meter-option" :class="{ active: formData.hasSmartMeter === true }">
                    <input type="radio" v-model="formData.hasSmartMeter" :value="true">
                    <div class="meter-card">
                      <i class="fas fa-wifi"></i>
                      <h4>Smart Meter vorhanden</h4>
                      <p>Ich kann meine Verbrauchsdaten hochladen</p>
                    </div>
                  </label>
                  
                  <label class="meter-option" :class="{ active: formData.hasSmartMeter === false }">
                    <input type="radio" v-model="formData.hasSmartMeter" :value="false">
                    <div class="meter-card">
                      <i class="fas fa-calculator"></i>
                      <h4>Kein Smart Meter</h4>
                      <p>Ich gebe meine Daten manuell ein</p>
                    </div>
                  </label>
                </div>
                <div v-if="formData.hasSmartMeter === null" class="form-help text-red-600">
                  Bitte wählen Sie eine Option aus
                </div>
              </div>

              <!-- Smart Meter Section -->
              <div v-if="formData.hasSmartMeter === true" class="smart-meter-section">
               
                <div class="form-group">
                  <label class="form-label">Postleitzahl *</label>
                  <input 
                    type="text" 
                    v-model="formData.zipCode" 
                    class="form-input"
                    placeholder="z.B. 70173"
                    pattern="[0-9]{5}"
                    maxlength="5"
                    required
                  >
                  <div class="form-help">
                    Für Tarifverfügbarkeit in Ihrer Region
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Aktuelle Monatskosten (€)</label>
                  <input 
                    type="number" 
                    v-model="formData.currentCost" 
                    class="form-input"
                    placeholder="z.B. 100"
                    step="1"
                    min="0"
                  >
                  <div class="form-help">
                    Optional: Für Ersparnis-Berechnung (aktuelle monatliche Stromkosten)
                  </div>
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
                        accept=".csv"
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
                          Unterstützte Formate: CSV
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
              <div v-else-if="formData.hasSmartMeter === false" class="manual-input-section">
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


              </div>

              <!-- Common fields for manual input only -->
              <div v-if="formData.hasSmartMeter === false">
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
                  <label class="form-label">Postleitzahl *</label>
                  <input 
                    type="text" 
                    v-model="formData.zipCode" 
                    class="form-input"
                    placeholder="z.B. 80331"
                    pattern="[0-9]{5}"
                    maxlength="5"
                    required
                  >
                  <div class="form-help">
                    Für regionale Tarifverfügbarkeit (Pflichtfeld)
                  </div>
                </div>
                

                <div class="form-group">
                  <label class="form-label">Aktuelle Monatskosten (€)</label>
                  <input 
                    type="number" 
                    v-model="formData.currentCost" 
                    class="form-input"
                    placeholder="z.B. 100"
                    step="1"
                    min="0"
                  >
                  <div class="form-help">
                    Für Ersparnis-Berechnung (monatliche Stromkosten)
                  </div>
                </div>

              
            

              </div>

              <button type="submit" class="btn btn-primary w-full" :disabled="loading || formData.hasSmartMeter === null">
                <span v-if="loading" class="loading-spinner small"></span>
                <i v-else class="fas fa-chart-line"></i>
                {{ loading ? 'Analysiere Tarife...' : formData.hasSmartMeter === null ? 'Bitte Smart Meter Auswahl treffen' : 'Tarife finden' }}
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
                <span v-if="formData.currentCost"> | Aktuelle Kosten: {{ formData.currentCost }}€/Monat</span>
              </p>
              
              <!-- Backend Connection Indicator -->
              <div class="api-status">
                <div class="status-indicator success">
                  <i class="fas fa-server"></i>
                  <span>Live-Daten vom DYNERGY Backend</span>
                  <div class="status-dot"></div>
                </div>
              </div>
              
              <div class="sort-controls">
                <label>Sortieren nach:</label>
                <select v-model="sortBy" @change="sortResults" class="form-select">
                  <option value="monthly_cost">Monatskosten (niedrig → hoch)</option>
                  <option value="annual_cost">Jahreskosten (niedrig → hoch)</option>
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
                      <span v-else class="badge badge-fixed">
                        <i class="fas fa-lock"></i>
                        Festpreis
                      </span>
                      <span v-if="tariff.features && tariff.features.includes('green')" class="badge badge-green">
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
                      <span v-if="tariff.risk_level === 'low'" class="badge badge-success">
                        <i class="fas fa-shield-alt"></i>
                        Niedriges Risiko
                      </span>
                      <span v-if="tariff.risk_level === 'moderate'" class="badge badge-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        Moderates Risiko
                      </span>
                      <span v-if="tariff.risk_level === 'high'" class="badge badge-danger">
                        <i class="fas fa-exclamation-circle"></i>
                        Höheres Risiko
                      </span>
                      <span v-if="index === 0" class="badge badge-gold">
                        <i class="fas fa-star"></i>
                        Empfohlen
                      </span>
                    </div>
                  </div>

                  <div class="tariff-price">
                    <div class="monthly-cost-main">{{ tariff.monthly_cost.toFixed(2) }}€/Monat</div>
                    <div class="annual-cost-small">{{ tariff.annual_cost.toFixed(2) }}€/Jahr</div>
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
                      <span>Grundpreis: {{ tariff.base_price.toFixed(2) }}€/Monat</span>
                    </div>
                    <div class="detail-item">
                      <i class="fas fa-bolt"></i>
                      <span>Arbeitspreis{{ tariff.is_dynamic ? ' (Ø)' : '' }}: {{ tariff.kwh_price.toFixed(4) }}€/kWh</span>
                    </div>
                    <div class="detail-item">
                      <i class="fas fa-calendar"></i>
                      <span>Laufzeit: 1 Monat</span>
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

                  <!-- Erweiterte Kosten-/Ersparnisinfo -->
                  <div class="cost-breakdown">
                    <h4><i class="fas fa-calculator"></i> Kostenaufschlüsselung</h4>
                    <div class="breakdown-grid">
                      <div class="breakdown-item">
                        <span class="breakdown-label">Grundgebühr/Jahr:</span>
                        <span class="breakdown-value">{{ (tariff.base_price * 12).toFixed(2) }}€</span>
                      </div>
                      <div class="breakdown-item">
                        <span class="breakdown-label">Verbrauchskosten/Jahr:</span>
                        <span class="breakdown-value">{{ (tariff.annual_cost - (tariff.base_price * 12)).toFixed(2) }}€</span>
                      </div>
                      <div v-if="formData.currentCost && (formData.currentCost * 12) > tariff.annual_cost" class="breakdown-item highlight">
                        <span class="breakdown-label">Einsparungspotenzial:</span>
                        <span class="breakdown-value savings">
                          {{ ((formData.currentCost * 12) - tariff.annual_cost).toFixed(2) }}€/Jahr
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Bester Tarif Hervorhebung -->
                  <div v-if="index === 0" class="best-deal-info">
                    <div class="best-deal-badge">
                      <i class="fas fa-trophy"></i>
                      <span>Bester Tarif für Ihr Profil</span>
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
                  
                  <div v-if="tariff.special_features && tariff.special_features.length > 0" class="special-features">
                    <h4><i class="fas fa-star"></i> Besondere Leistungen</h4>
                    <ul>
                      <li v-for="feature in tariff.special_features" :key="feature">
                        <i class="fas fa-check text-green-600"></i>
                        {{ translateFeature(feature) }}
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- Einsparungsinfos -->
                <div v-if="tariff.is_dynamic" class="optimization-savings">
                  <div class="optimization-header">
                    <i class="fas fa-chart-line"></i>
                    <span>Smart-Optimierung möglich</span>
                  </div>
                  <div class="optimization-details">
                    <div class="optimization-item">
                      <i class="fas fa-moon"></i>
                      <span>Nachtverbrauch: bis zu 15% günstiger</span>
                    </div>
                    <div class="optimization-item">
                      <i class="fas fa-mobile-alt"></i>
                      <span>App-Benachrichtigungen für günstige Stunden</span>
                    </div>
                    <div class="optimization-item">
                      <i class="fas fa-piggy-bank"></i>
                      <span>Zusätzliche Ersparnis: {{ (tariff.annual_cost * (0.10 + Math.random() * 0.15)).toFixed(2) }}€/Jahr</span>
                    </div>
                  </div>
                </div>

                <!-- Ersparnis gegenüber aktuellem Tarif (nur bei Einsparungen) -->
                <div v-if="formData.currentCost && formData.currentCost > tariff.annual_cost" class="current-savings">
                  <div class="savings-header">
                    <i class="fas fa-arrow-down"></i>
                    <span>Ihre Ersparnis gegenüber aktuellem Tarif</span>
                  </div>
                  <div class="savings-amount-large">
                    {{ (formData.currentCost - tariff.annual_cost).toFixed(2) }}€ pro Jahr
                  </div>
                  <div class="savings-breakdown-small">
                    <span>Das sind {{ ((formData.currentCost - tariff.annual_cost) / 12).toFixed(2) }}€ pro Monat weniger</span>
                  </div>
                  <div class="savings-percentage">
                    {{ (((formData.currentCost - tariff.annual_cost) / formData.currentCost) * 100).toFixed(1) }}% Ersparnis
                  </div>
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

          <!-- Prognose und Vorhersage Sektion -->
          <div v-if="results.length > 0 && !loading" class="forecast-section">
            <div class="forecast-cards">
              <!-- Preisvorhersage -->
              <div class="forecast-card forecast-card-full">
                <div class="forecast-header">
                  <h4>
                    <i class="fas fa-chart-line"></i>
                    7-Tage Strompreis-Prognose
                  </h4>
                </div>
                <div class="forecast-content">
                  <div v-if="priceForecast" class="price-forecast">
                    <div class="forecast-chart">
                      <div v-for="day in priceForecast.slice(0, 7)" :key="day.date" class="day-forecast">
                        <div class="day-name">{{ getDayName(day.day_name) }}</div>
                        <div class="price-range">
                          <span class="min-price">{{ (day.min_price * 1000).toFixed(1) }}ct</span>
                          <div class="price-bar">
                            <div class="price-fill" :style="{ width: getPriceBarWidth(day) + '%' }"></div>
                          </div>
                          <span class="max-price">{{ (day.max_price * 1000).toFixed(1) }}ct</span>
                        </div>
                        <div class="price-avg">Ø {{ (day.avg_price * 1000).toFixed(1) }}ct</div>
                      </div>
                    </div>
                    <div class="forecast-summary">
                      <p><strong>Günstigste Stunden:</strong> {{ priceForecast[0]?.best_hours || 'Nachts 23:00-06:00 Uhr' }}</p>
                      <p><strong>Teuerste Stunden:</strong> {{ priceForecast[0]?.worst_hours || 'Abends 17:00-20:00 Uhr' }}</p>
                    </div>
                  </div>
                  <div v-else class="loading-forecast">
                    <div class="loading-spinner small"></div>
                    <span>Lade Preisprognose...</span>
                  </div>
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

  <!-- Tariff Details Modal -->
  <div v-if="showDetailsModal" class="modal-overlay" @click="closeDetailsModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ selectedTariff?.name }} - Detailansicht</h2>
        <button class="modal-close" @click="closeDetailsModal">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body" v-if="selectedTariff">
        <div class="tariff-overview">
          <div class="overview-grid">
            <div class="overview-item">
              <h3>{{ selectedTariff.provider }}</h3>
              
              <!-- All Badges in one row -->
              <div class="tariff-badges">
                <span v-if="selectedTariff.is_dynamic" class="badge badge-dynamic">
                  <i class="fas fa-chart-line"></i>
                  Dynamisch
                </span>
                <span v-else class="badge badge-fixed">
                  <i class="fas fa-lock"></i>
                  Fester Tarif
                </span>
                
                <span v-if="selectedTariff.features && selectedTariff.features.includes('green')" class="badge badge-green">
                  <i class="fas fa-leaf"></i>
                  Ökostrom
                </span>
                <span v-if="selectedTariff.app_available" class="badge badge-tech">
                  <i class="fas fa-mobile-alt"></i>
                  App
                </span>
                <span v-if="selectedTariff.automation_ready" class="badge badge-smart">
                  <i class="fas fa-home"></i>
                  Smart Ready
                </span>
                <span v-if="selectedTariff.risk_level === 'low'" class="badge badge-success">
                  <i class="fas fa-shield-alt"></i>
                  Niedriges Risiko
                </span>
                <span v-if="selectedTariff.risk_level === 'moderate'" class="badge badge-warning">
                  <i class="fas fa-exclamation-triangle"></i>
                  Moderates Risiko
                </span>
                <span v-if="selectedTariff.risk_level === 'high'" class="badge badge-danger">
                  <i class="fas fa-exclamation-circle"></i>
                  Höheres Risiko
                </span>
              </div>
            </div>
            
            <div class="overview-item">
              <div class="cost-display">
                <div class="monthly-cost">{{ selectedTariff.monthly_cost }}€</div>
                <div class="cost-label">pro Monat</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Detaillierte Informationen in 3-spaltigem Layout -->
        <div class="modal-info-grid">
          <!-- Tarif Details -->
          <div class="detail-section">
            <h3><i class="fas fa-info-circle"></i> Tarifdetails</h3>
            <div class="detail-list">
              <div class="detail-row">
                <span class="label">Grundpreis:</span>
                <span class="value">{{ selectedTariff.base_price }}€/Monat</span>
              </div>
              <div class="detail-row">
                <span class="label">Arbeitspreis{{ selectedTariff.is_dynamic ? ' (Ø)' : '' }}:</span>
                <span class="value">{{ selectedTariff.kwh_price.toFixed(4) }}€/kWh</span>
              </div>
              <div class="detail-row">
                <span class="label">Vertragslaufzeit:</span>
                <span class="value">{{ selectedTariff.contract_duration }} Monate</span>
              </div>
              <div class="detail-row">
                <span class="label">Kündigungsfrist:</span>
                <span class="value">{{ selectedTariff.contract_duration > 1 ? '6 Wochen' : '2 Wochen' }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Preisgarantie:</span>
                <span class="value">{{ selectedTariff.is_dynamic ? 'Keine (dynamisch)' : '12 Monate' }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Ökostrom:</span>
                <span class="value">
                  <i v-if="selectedTariff.green_energy" class="fas fa-check text-green-600"></i>
                  <i v-else class="fas fa-times text-red-600"></i>
                  {{ selectedTariff.green_energy ? '100% Ökostrom' : 'Konventioneller Strom' }}
                </span>
              </div>
              <div class="detail-row highlight-row">
                <span class="label">Jährliche Kosten:</span>
                <span class="value highlight">{{ Math.round(selectedTariff.annual_cost) }}€</span>
              </div>
            </div>
            
            <!-- Tarifmerkmale -->
            <div class="features-list">
              <h4><i class="fas fa-star"></i> Tarifmerkmale</h4>
              <ul>
                <li v-if="selectedTariff.is_dynamic">
                  <i class="fas fa-chart-line"></i>
                  <span>Dynamischer Stromtarif mit stündlich variablen Preisen</span>
                </li>
                <li v-if="selectedTariff.features && selectedTariff.features.includes('green')">
                  <i class="fas fa-leaf"></i>
                  <span>100% Ökostrom aus erneuerbaren Energien</span>
                </li>
                <li v-if="selectedTariff.app_available">
                  <i class="fas fa-mobile-alt"></i>
                  <span>App-Steuerung mit Preisbenachrichtigungen möglich</span>
                </li>
                <li v-if="selectedTariff.automation_ready">
                  <i class="fas fa-home"></i>
                  <span>Smart Home Integration für automatische Verbrauchssteuerung</span>
                </li>
                <li v-if="!selectedTariff.is_dynamic">
                  <i class="fas fa-lock"></i>
                  <span>Fester Strompreis - keine Preisschwankungen</span>
                </li>
                <li v-if="selectedTariff.contract_duration === 1">
                  <i class="fas fa-calendar-check"></i>
                  <span>Flexible Laufzeit - monatlich kündbar</span>
                </li>
                <li v-if="selectedTariff.risk_level === 'low'" class="risk-info-low">
                  <i class="fas fa-shield-alt"></i>
                  <span>Niedriges Risiko - geringe Abweichungen vom geschätzten Preis erwartet</span>
                  <button 
                    v-if="selectedTariff.risk_factors && selectedTariff.risk_factors.length > 0"
                    @click="scrollToRiskBreakdown"
                    class="risk-info-button"
                    title="Zur detaillierten Risikoanalyse"
                  >
                    <i class="fas fa-info-circle"></i>
                  </button>
                </li>
                <li v-if="selectedTariff.risk_level === 'moderate'" class="risk-info-moderate">
                  <i class="fas fa-exclamation-triangle"></i>
                  <span>Moderates Risiko - signifikante Abweichungen vom geschätzten Preis möglich</span>
                  <button 
                    v-if="selectedTariff.risk_factors && selectedTariff.risk_factors.length > 0"
                    @click="scrollToRiskBreakdown"
                    class="risk-info-button"
                    title="Zur detaillierten Risikoanalyse"
                  >
                    <i class="fas fa-info-circle"></i>
                  </button>
                </li>
                <li v-if="selectedTariff.risk_level === 'high'" class="risk-info-high">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>Höheres Risiko - starke Abweichungen vom geschätzten Preis wahrscheinlich</span>
                  <button 
                    v-if="selectedTariff.risk_factors && selectedTariff.risk_factors.length > 0"
                    @click="scrollToRiskBreakdown"
                    class="risk-info-button"
                    title="Zur detaillierten Risikoanalyse"
                  >
                    <i class="fas fa-info-circle"></i>
                  </button>
                </li>
              </ul>
            </div>
          </div>

          <!-- Kostenaufschlüsselung -->
          <div class="cost-section">
            <h3><i class="fas fa-calculator"></i> Kostenaufschlüsselung</h3>
            <div class="cost-breakdown-detail">
              <div class="cost-item">
                <div class="cost-label">Grundgebühr (jährlich)</div>
                <div class="cost-value">{{ Math.round(selectedTariff.base_price * 12) }}€</div>
                <div class="cost-percentage">{{ Math.round(((selectedTariff.base_price * 12) / selectedTariff.annual_cost) * 100) }}%</div>
              </div>
              <div class="cost-item">
                <div class="cost-label">Verbrauchskosten ({{ formData.annualKwh }} kWh)</div>
                <div class="cost-value">{{ Math.round(selectedTariff.annual_cost - (selectedTariff.base_price * 12)) }}€</div>
                <div class="cost-percentage">{{ Math.round(((selectedTariff.annual_cost - (selectedTariff.base_price * 12)) / selectedTariff.annual_cost) * 100) }}%</div>
              </div>
              <div class="cost-separator"></div>
              <div class="cost-item total">
                <div class="cost-label">Gesamtkosten pro Jahr</div>
                <div class="cost-value">{{ Math.round(selectedTariff.annual_cost) }}€</div>
                <div class="cost-percentage">100%</div>
              </div>
            </div>

            <div class="cost-comparison">
              <h4><i class="fas fa-chart-bar"></i> Kostenvergleich</h4>
              <div class="comparison-item">
                <span class="comparison-label">Pro kWh (Durchschnitt):</span>
                <span class="comparison-value">{{ (selectedTariff.annual_cost / formData.annualKwh).toFixed(3) }}€</span>
              </div>
              <div class="comparison-item">
                <span class="comparison-label">Pro Monat:</span>
                <span class="comparison-value">{{ Math.round(selectedTariff.annual_cost / 12) }}€</span>
              </div>
              <div class="comparison-item">
                <span class="comparison-label">Pro Tag:</span>
                <span class="comparison-value">{{ (selectedTariff.annual_cost / 365).toFixed(2) }}€</span>
              </div>
            </div>

            <!-- Einsparungspotenzial für dynamische Tarife -->
            <div v-if="selectedTariff.is_dynamic" class="optimization-potential">
              <h4><i class="fas fa-lightbulb"></i> Smart-Optimierung</h4>
              <div class="optimization-stats">
                <div class="stat-item">
                  <div class="stat-icon"><i class="fas fa-moon"></i></div>
                  <div class="stat-content">
                    <div class="stat-title">Nachtverbrauch</div>
                    <div class="stat-value">bis -25%</div>
                  </div>
                </div>
                <div class="stat-item">
                  <div class="stat-icon"><i class="fas fa-mobile-alt"></i></div>
                  <div class="stat-content">
                    <div class="stat-title">App-Steuerung</div>
                    <div class="stat-value">bis -15%</div>
                  </div>
                </div>
                <div class="stat-item">
                  <div class="stat-icon"><i class="fas fa-home"></i></div>
                  <div class="stat-content">
                    <div class="stat-title">Smart Home</div>
                    <div class="stat-value">bis -20%</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Vertragsinformationen -->
          <div class="contract-section">
            <h3><i class="fas fa-file-contract"></i> Vertragsinformationen</h3>
            <div class="contract-details">
              <div class="contract-item">
                <i class="fas fa-calendar-alt"></i>
                <div class="contract-content">
                  <div class="contract-title">Mindestlaufzeit</div>
                  <div class="contract-value">1 Monat</div>
                </div>
              </div>
              <div class="contract-item">
                <i class="fas fa-clock"></i>
                <div class="contract-content">
                  <div class="contract-title">Kündigungsfrist</div>
                  <div class="contract-value">{{ selectedTariff.contract_duration > 1 ? '6 Wochen zum Monatsende' : '2 Wochen zum Monatsende' }}</div>
                </div>
              </div>
              <div class="contract-item">
                <i class="fas fa-shield-alt"></i>
                <div class="contract-content">
                  <div class="contract-title">Preisgarantie</div>
                  <div class="contract-value">{{ selectedTariff.is_dynamic ? 'Keine (marktbasiert)' : '12 Monate' }}</div>
                </div>
              </div>
            </div>

            <!-- Anbieter-Info -->
            <div class="provider-info">
              <h4><i class="fas fa-building"></i> Anbieter</h4>
              <div class="provider-details">
                <div class="provider-logo">
                  <div class="logo-placeholder">{{ selectedTariff.provider }}</div>
                </div>
                <div class="provider-content">
                  <div class="provider-name">{{ selectedTariff.provider }}</div>
                  <div class="provider-description">
                    {{ getProviderDescription(selectedTariff.provider) }}
                  </div>
                  <div class="provider-rating">
                    <span class="rating-stars">
                      <i class="fas fa-star"></i>
                      <i class="fas fa-star"></i>
                      <i class="fas fa-star"></i>
                      <i class="fas fa-star"></i>
                      <i class="far fa-star"></i>
                    </span>
                    <span class="rating-text">4.2/5 (Kundenbewertung)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Diagramme untereinander -->
        <div class="charts-container">
          <h3 class="charts-title"><i class="fas fa-chart-line"></i> Prognose & Analyse</h3>
          <div class="charts-grid">
            <!-- Risk Analysis Box (replaces Einsparungspotenzial) -->
            <div class="chart-section">
              <h4><i class="fas fa-shield-alt"></i> Risikoanalyse</h4>
              
              <div v-if="!uploadedFile" class="chart-placeholder">
                <div class="placeholder-content">
                  <div class="no-data-state">
                    <i class="fas fa-chart-line"></i>
                    <p>Laden Sie Ihre Verbrauchsdaten hoch, um eine Risikoanalyse zu sehen</p>
                  </div>
                </div>
              </div>
              
              <div v-else-if="riskAnalysisLoading" class="chart-placeholder">
                <div class="placeholder-content">
                  <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Lade Risikoanalyse...</p>
                  </div>
                </div>
              </div>
              
              <div v-else-if="riskAnalysisError" class="chart-placeholder">
                <div class="placeholder-content">
                  <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>{{ riskAnalysisError }}</p>
                  </div>
                </div>
              </div>
              
              <div v-else-if="riskAnalysisData" class="risk-analysis-content">
                <!-- Only show these metrics for dynamic tariffs -->
                <!-- Historic Risk Summary -->
                <div v-if="selectedTariff.is_dynamic" class="risk-summary-card">
                  <div class="risk-summary-header">
                    <i class="fas fa-history"></i>
                    <span>Historisches Risiko</span>
                  </div>
                  <div class="risk-summary-body">
                    <div class="risk-stat">
                      <span class="stat-label">Markt Ø</span>
                      <span class="stat-value">{{ (riskAnalysisData.historic_risk.market_avg_price * 1000).toFixed(2) }} ct/kWh</span>
                    </div>
                    <div class="risk-stat">
                      <span class="stat-label">Ihr Ø</span>
                      <span class="stat-value">{{ (riskAnalysisData.historic_risk.user_weighted_price * 1000).toFixed(2) }} ct/kWh</span>
                    </div>
                    <div class="risk-stat highlight">
                      <span class="stat-label">Differenz</span>
                      <span class="stat-value" :class="{
                        'text-success': riskAnalysisData.historic_risk.risk_exposure === 'favorable',
                        'text-danger': riskAnalysisData.historic_risk.risk_exposure === 'unfavorable'
                      }">
                        {{ riskAnalysisData.historic_risk.price_differential_pct > 0 ? '+' : '' }}{{ riskAnalysisData.historic_risk.price_differential_pct.toFixed(1) }}%
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Coincidence Factor Summary -->
                <div v-if="selectedTariff.is_dynamic" class="risk-summary-card">
                  <div class="risk-summary-header">
                    <i class="fas fa-chart-pie"></i>
                    <span>Koinzidenzfaktor</span>
                  </div>
                  <div class="risk-summary-body">
                    <div class="coincidence-display">
                      <div class="coincidence-circle-small" :class="{
                        'circle-success': riskAnalysisData.coincidence_factor.coincidence_rating === 'low',
                        'circle-warning': riskAnalysisData.coincidence_factor.coincidence_rating === 'medium',
                        'circle-danger': riskAnalysisData.coincidence_factor.coincidence_rating === 'high'
                      }">
                        <span class="circle-value">{{ riskAnalysisData.coincidence_factor.consumption_coincidence_pct.toFixed(0) }}%</span>
                      </div>
                      <div class="coincidence-info">
                        <div class="info-text">
                          Sie verbrauchen {{ riskAnalysisData.coincidence_factor.consumption_during_expensive_hours }} kWh, das sind {{ riskAnalysisData.coincidence_factor.consumption_coincidence_pct.toFixed(0) }}% Ihres täglichen Verbrauchs, in den teuersten Stunden.
                        </div>
                        <div class="info-badge" :class="{
                          'badge-success': riskAnalysisData.coincidence_factor.coincidence_rating === 'low',
                          'badge-warning': riskAnalysisData.coincidence_factor.coincidence_rating === 'medium',
                          'badge-danger': riskAnalysisData.coincidence_factor.coincidence_rating === 'high'
                        }">
                          {{ riskAnalysisData.coincidence_factor.coincidence_rating === 'low' ? 'Günstig' : riskAnalysisData.coincidence_factor.coincidence_rating === 'medium' ? 'Neutral' : 'Ungünstig' }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Load Profile Chart -->
                <div v-if="selectedTariff.is_dynamic" class="risk-chart-card">
                  <div class="risk-summary-header">
                    <i class="fas fa-chart-area"></i>
                    <span>Lastprofil & Preiskorrelation</span>
                  </div>
                  <div class="risk-chart-body">
                    <LoadProfileChart :loadProfileData="riskAnalysisData.load_profile" />
                  </div>
                </div>

                <!-- Message for fixed tariffs -->
                <div v-if="!selectedTariff.is_dynamic" class="fixed-tariff-note">
                  <div class="info-banner">
                    <i class="fas fa-info-circle"></i>
                    <p>
                      Bei Festpreistarifen sind die historische Risikoanalyse, der Koinzidenzfaktor und die 
                      Preisvolatilität nicht relevant, da die Preise nicht vom Markt abhängig sind.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Backtest Chart -->
            <div class="chart-section">
              <h4><i class="fas fa-chart-area"></i> Verbrauchsprognose Backtest</h4>
              <BacktestChart :uploadedFile="uploadedFile" />
            </div>
          </div>
        </div>

        <!-- Detailed Risk Breakdown -->
        <div v-if="selectedTariff.risk_factors && selectedTariff.risk_factors.length > 0" id="risk-breakdown" class="risk-breakdown-section">
          <h3 class="risk-breakdown-title">
            <i class="fas fa-analytics"></i>
            Detaillierte Risikoanalyse
          </h3>
          
          <div class="risk-overview-card">
            <div class="risk-score-display">
              <div class="risk-score-circle" :class="{
                'score-low': selectedTariff.risk_level === 'low',
                'score-moderate': selectedTariff.risk_level === 'moderate',
                'score-high': selectedTariff.risk_level === 'high'
              }">
                <span class="score-number">{{ selectedTariff.risk_score }}</span>
                <span class="score-label">/ 100</span>
              </div>
              <div class="risk-score-info">
                <div class="risk-level-badge" :class="{
                  'badge-success': selectedTariff.risk_level === 'low',
                  'badge-warning': selectedTariff.risk_level === 'moderate',
                  'badge-danger': selectedTariff.risk_level === 'high'
                }">
                  {{ selectedTariff.risk_level === 'low' ? 'Niedriges Risiko' : selectedTariff.risk_level === 'moderate' ? 'Moderates Risiko' : 'Höheres Risiko' }}
                </div>
                <p class="risk-message">{{ selectedTariff.risk_message }}</p>
              </div>
            </div>
          </div>

          <div class="risk-factors-grid">
            <div 
              v-for="(factor, index) in selectedTariff.risk_factors" 
              :key="index"
              class="risk-factor-card"
              :class="{
                'factor-positive': factor.impact === 'positive',
                'factor-neutral': factor.impact === 'neutral',
                'factor-negative': factor.impact === 'negative'
              }"
            >
              <div class="factor-header">
                <div class="factor-icon">
                  <i v-if="factor.impact === 'positive'" class="fas fa-check-circle"></i>
                  <i v-else-if="factor.impact === 'neutral'" class="fas fa-minus-circle"></i>
                  <i v-else class="fas fa-exclamation-circle"></i>
                </div>
                <h4 class="factor-title">{{ factor.factor }}</h4>
              </div>
              <p class="factor-detail">{{ factor.detail }}</p>
              <div class="factor-impact-label">
                <span v-if="factor.impact === 'positive'">Positiver Einfluss</span>
                <span v-else-if="factor.impact === 'neutral'">Neutraler Einfluss</span>
                <span v-else>Negativer Einfluss</span>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-primary" @click="selectTariff(selectedTariff)">
            <i class="fas fa-check"></i>
            Diesen Tarif wählen
          </button>
          <button class="btn btn-secondary" @click="closeDetailsModal">
            <i class="fas fa-times"></i>
            Schließen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import BacktestChart from '../components/BacktestChart.vue'
import LoadProfileChart from '../components/LoadProfileChart.vue'
import { apiService } from '../services/api'

export default {
  name: 'TariffComparison',
  components: {
    BacktestChart,
    LoadProfileChart
  },
  setup() {
    const formData = ref({
      hasSmartMeter: null, // Start with null to force user selection
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
    const sortBy = ref('monthly_cost')
    
    // File upload functionality
    const uploadedFile = ref(null)
    const csvData = ref(null)
    const fileError = ref('')
    const isDragOver = ref(false)
    
    // Prognose data
    const priceForecast = ref(null)
    
    // Risk analysis data
    const riskAnalysisData = ref(null)
    const riskAnalysisLoading = ref(false)
    const riskAnalysisError = ref(null)
    
    // Modal functionality
    const showDetailsModal = ref(false)
    const selectedTariff = ref(null)
    
    const sortedResults = computed(() => {
      const sorted = [...results.value]
      
      switch (sortBy.value) {
        case 'monthly_cost':
          return sorted.sort((a, b) => a.monthly_cost - b.monthly_cost)
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
            return a.monthly_cost - b.monthly_cost
          })
        default:
          return sorted
      }
    })
    
    const calculateTariffs = async () => {
      loading.value = true
      searchPerformed.value = true
      
      try {
        const zipCode = formData.value.zipCode
        let annualConsumption = formData.value.annualKwh
        let csvAnalysis = null
        
        // Check if user uploaded a CSV file - analyze it FIRST
        if (formData.value.hasSmartMeter && uploadedFile.value) {
          console.log('📊 Analyzing uploaded CSV file:', uploadedFile.value.name)
          
          try {
            const csvResponse = await apiService.calculateWithCsv(uploadedFile.value)
            const csvData = csvResponse.data
            console.log('✅ CSV analysis complete:', csvData)
            
            // Extract annual consumption from CSV
            if (csvData.annual_kwh) {
              annualConsumption = Math.round(csvData.annual_kwh)
              formData.value.annualKwh = annualConsumption
              console.log(`Updated annual consumption from CSV: ${annualConsumption} kWh`)
            }
            
            // Store CSV analysis for later use
            csvAnalysis = csvData
            
            // Fetch risk analysis with CSV data BEFORE creating tariffs
            console.log('Fetching risk analysis before tariff creation...')
            try {
              // Fetch full risk analysis (for charts/details)
              const riskResponse = await apiService.getRiskAnalysis(uploadedFile.value, 30)
              riskAnalysisData.value = riskResponse.data
              
              // ALSO fetch risk score (for badges)
              const riskScoreResponse = await apiService.getRiskScore(uploadedFile.value, 30)
              const riskScore = riskScoreResponse.data
              
              // Merge risk score into risk analysis data
              riskAnalysisData.value.risk_level = riskScore.risk_level
              riskAnalysisData.value.risk_score = riskScore.risk_score
              riskAnalysisData.value.risk_message = riskScore.risk_message
              
              console.log('Risk analysis loaded:', riskAnalysisData.value)
              console.log('Risk level:', riskAnalysisData.value.risk_level)
              console.log('Risk score:', riskAnalysisData.value.risk_score)
            } catch (riskError) {
              console.error('⚠️ Risk analysis failed:', riskError)
              riskAnalysisData.value = null
            }
          } catch (csvError) {
            console.error('⚠️ CSV analysis failed:', csvError)
          }
        }
        
        console.log(`🔍 Scraping tariffs for PLZ: ${zipCode}, Consumption: ${annualConsumption} kWh`)
        
        // Call combined scraper endpoint with actual consumption data
        // Pass CSV file if available for per-tariff risk analysis
        const scraperOptions = {}
        if (uploadedFile.value) {
          scraperOptions.csvFile = uploadedFile.value
          scraperOptions.days = 30
          console.log('📊 Sending CSV file to scraper for per-tariff risk analysis')
        }
        
        const scraperResponse = await apiService.scrapeAllTariffs(
          zipCode, 
          annualConsumption, 
          ['enbw', 'enbw_strom', 'tado', 'tibber'],
          scraperOptions
        )
        const scraperData = scraperResponse.data
        
        console.log('✅ Scraper response:', scraperData)
        
        // If no CSV was uploaded, fetch simplified risk scores for dynamic and fixed tariffs
        let simplifiedRiskDynamic = null
        let simplifiedRiskFixed = null
        if (!uploadedFile.value && annualConsumption) {
          console.log('📊 No CSV uploaded - fetching simplified risk scores')
          try {
            const riskDynamicResponse = await apiService.getRiskScoreYearlyUsage(annualConsumption, true)
            simplifiedRiskDynamic = riskDynamicResponse.data
            console.log('Dynamic risk (simplified):', simplifiedRiskDynamic)
            
            const riskFixedResponse = await apiService.getRiskScoreYearlyUsage(annualConsumption, false)
            simplifiedRiskFixed = riskFixedResponse.data
            console.log('Fixed risk (simplified):', simplifiedRiskFixed)
          } catch (riskError) {
            console.error('⚠️ Simplified risk score failed:', riskError)
          }
        }
        
        if (scraperData.success && scraperData.tariffs && scraperData.tariffs.length > 0) {
          // Lade Forecast-Daten für dynamische Preisberechnung
          let forecastAvgPrice = 0.25  // Default fallback in €/kWh
          try {
            const forecastResponse = await apiService.getForecast()
            if (forecastResponse && forecastResponse.data && forecastResponse.data.forecast) {
              const forecastData = forecastResponse.data.forecast
              // Calculate average from all hourly prices across all days
              let allPrices = []
              forecastData.forEach(day => {
                day.hourly_prices.forEach(hour => {
                  allPrices.push(hour.price)
                })
              })
              forecastAvgPrice = allPrices.reduce((a, b) => a + b, 0) / allPrices.length
              console.log(`📈 Forecast average price: ${forecastAvgPrice.toFixed(4)} €/kWh (${(forecastAvgPrice * 100).toFixed(2)} ct/kWh)`)
            }
          } catch (forecastError) {
            console.warn('⚠️ Could not fetch forecast data, using fallback price:', forecastError)
          }
          
          // Convert EnergyTariff format to frontend display format
          const scrapedTariffs = scraperData.tariffs.map(tariff => {
            // Debug: Log features from backend
            console.log(`📦 ${tariff.name} features from backend:`, tariff.features)
            
            const monthlyConsumption = annualConsumption / 12
            let monthlyCost, annualCost, totalKwhPrice
            
            // Check if this is a fixed or dynamic tariff
            if (tariff.is_dynamic === false && tariff.kwh_rate) {
              // FIXED TARIFF: Simple calculation with fixed kWh rate
              const fixedKwhRate = tariff.kwh_rate
              monthlyCost = tariff.base_price + (monthlyConsumption * fixedKwhRate)
              annualCost = (tariff.base_price * 12) + (annualConsumption * fixedKwhRate)
              totalKwhPrice = fixedKwhRate
              
              console.log(`💰 ${tariff.name} (FIXED) Berechnung:`)
              console.log(`   Grundpreis: ${tariff.base_price}€/Monat`)
              console.log(`   Fixpreis: ${fixedKwhRate}€/kWh = ${(fixedKwhRate * 100).toFixed(2)} ct/kWh`)
              console.log(`   Monatlicher Verbrauch: ${monthlyConsumption.toFixed(2)} kWh`)
              console.log(`   Monatspreis gesamt: ${monthlyCost.toFixed(2)}€`)
              console.log(`   Jahrespreis gesamt: ${annualCost.toFixed(2)}€`)
              
            } else if (tariff.provider === "Tibber" && tariff.additional_kwh_rate) {
              // DYNAMIC TARIFF - Tibber: Grundpreis + (Verbrauch × Arbeitspreis) + (Verbrauch × Forecast)
              const additionalCost = forecastAvgPrice * monthlyConsumption
              const taxesCost = tariff.additional_kwh_rate * monthlyConsumption
              monthlyCost = tariff.base_price + additionalCost + taxesCost
              annualCost = (tariff.base_price * 12) + (forecastAvgPrice * annualConsumption) + (tariff.additional_kwh_rate * annualConsumption)
              totalKwhPrice = forecastAvgPrice + tariff.additional_kwh_rate
              
              console.log(`💰 ${tariff.provider} (DYNAMIC) Berechnung:`)
              console.log(`   Grundpreis: ${tariff.base_price}€/Monat`)
              console.log(`   Arbeitspreis (Umlagen/Steuern): ${tariff.additional_kwh_rate}€/kWh = ${(tariff.additional_kwh_rate * 100).toFixed(2)} ct/kWh`)
              console.log(`   Börsenpreis (Forecast): ${forecastAvgPrice.toFixed(4)}€/kWh = ${(forecastAvgPrice * 100).toFixed(2)} ct/kWh`)
              console.log(`   ➜ Gesamt-kWh-Preis: ${totalKwhPrice.toFixed(4)}€/kWh = ${(totalKwhPrice * 100).toFixed(2)} ct/kWh`)
              console.log(`   Monatlicher Verbrauch: ${monthlyConsumption.toFixed(2)} kWh`)
              console.log(`   Umlagen/Steuern-Kosten/Monat: ${taxesCost.toFixed(2)}€`)
              console.log(`   Börsenstrom-Kosten/Monat: ${additionalCost.toFixed(2)}€`)
              console.log(`   Monatspreis gesamt: ${monthlyCost.toFixed(2)}€`)
              console.log(`   Jahrespreis gesamt: ${annualCost.toFixed(2)}€`)
              
            } else {
              // DYNAMIC TARIFF - EnBW, Tado: Grundpreis + (Forecast × Verbrauch) + (Arbeitspreis × Verbrauch)
              const forecastCost = forecastAvgPrice * monthlyConsumption
              const arbeitspreisCtKwh = (tariff.additional_price_ct_kwh || 0) / 100  // ct/kWh → €/kWh
              const arbeitspreisCost = arbeitspreisCtKwh * monthlyConsumption
              monthlyCost = tariff.base_price + forecastCost + arbeitspreisCost
              annualCost = (tariff.base_price * 12) + (forecastAvgPrice * annualConsumption) + (arbeitspreisCtKwh * annualConsumption)
              totalKwhPrice = forecastAvgPrice + arbeitspreisCtKwh
              
              console.log(`💰 ${tariff.provider} (DYNAMIC) Berechnung:`)
              console.log(`   Grundpreis: ${tariff.base_price}€/Monat`)
              console.log(`   Arbeitspreis (vom Scraper): ${tariff.additional_price_ct_kwh || 0} ct/kWh = ${arbeitspreisCtKwh.toFixed(4)}€/kWh`)
              console.log(`   Börsenpreis (Forecast): ${forecastAvgPrice.toFixed(4)}€/kWh = ${(forecastAvgPrice * 100).toFixed(2)} ct/kWh`)
              console.log(`   ➜ Gesamt-kWh-Preis: ${totalKwhPrice.toFixed(4)}€/kWh = ${(totalKwhPrice * 100).toFixed(2)} ct/kWh`)
              console.log(`   Monatlicher Verbrauch: ${monthlyConsumption.toFixed(2)} kWh`)
              console.log(`   Arbeitspreis-Kosten/Monat: ${arbeitspreisCost.toFixed(2)}€`)
              console.log(`   Forecast-Kosten/Monat: ${forecastCost.toFixed(2)}€`)
              console.log(`   Monatspreis gesamt: ${monthlyCost.toFixed(2)}€`)
              console.log(`   Jahrespreis gesamt: ${annualCost.toFixed(2)}€`)
            }
            
            // Determine which risk assessment to use
            let tariffRiskLevel, tariffRiskScore, tariffRiskMessage, tariffRiskFactors
            
            if (tariff.risk_level) {
              // Use per-tariff risk from backend (CSV uploaded)
              tariffRiskLevel = tariff.risk_level
              tariffRiskScore = tariff.risk_score
              tariffRiskMessage = tariff.risk_message
              tariffRiskFactors = tariff.risk_factors || []
            } else if (uploadedFile.value && riskAnalysisData.value?.risk_level) {
              // Use global risk from CSV analysis
              tariffRiskLevel = riskAnalysisData.value.risk_level
              tariffRiskScore = riskAnalysisData.value.risk_score
              tariffRiskMessage = riskAnalysisData.value.risk_message
              tariffRiskFactors = riskAnalysisData.value.risk_factors || []
            } else if (!uploadedFile.value) {
              // Use simplified risk scores for yearly usage (no CSV)
              const isDynamic = tariff.is_dynamic !== false
              const simplifiedRisk = isDynamic ? simplifiedRiskDynamic : simplifiedRiskFixed
              
              if (simplifiedRisk) {
                tariffRiskLevel = simplifiedRisk.risk_level
                tariffRiskScore = simplifiedRisk.risk_score
                tariffRiskMessage = simplifiedRisk.risk_message
                tariffRiskFactors = simplifiedRisk.risk_factors || []
              }
            }
            
            return {
              id: `${tariff.provider.toLowerCase()}-${tariff.is_dynamic ? 'dynamic' : 'fixed'}-${tariff.name.toLowerCase().replace(/\s+/g, '-')}`,
              name: tariff.name,
              provider: tariff.provider,
              monthly_cost: Math.round(monthlyCost),
              annual_cost: Math.round(annualCost),
              base_price: tariff.base_price,
              network_fee: tariff.network_fee || 0,
              kwh_price: totalKwhPrice,
              is_dynamic: tariff.is_dynamic !== false,  // Default to true if not specified
              smart_meter_required: tariff.is_dynamic !== false,
              green_energy: tariff.features?.includes('green') || false,
              app_available: tariff.features?.includes('app') || tariff.is_dynamic !== false,  // Check features first, then dynamic
              price_forecast: tariff.is_dynamic !== false,
              automation_ready: tariff.is_dynamic !== false,
              features: tariff.features || [],  // ← IMPORTANT: Pass through the features array!
              special_features: tariff.features || [],
              // Add CSV-based metrics if available
              csv_based: csvAnalysis !== null,
              actual_annual_consumption: csvAnalysis ? annualConsumption : null,
              // Risk assessment (from CSV, global, or simplified)
              risk_level: tariffRiskLevel,
              risk_score: tariffRiskScore,
              risk_message: tariffRiskMessage,
              risk_factors: tariffRiskFactors
            }
          })
          
          results.value = scrapedTariffs
          console.log('📊 Scraped tariffs with CSV data:', scrapedTariffs)
          
          // Log risk assessment status
          const tariffsWithRisk = scrapedTariffs.filter(t => t.risk_level).length
          if (tariffsWithRisk > 0) {
            console.log(`🛡️ Per-tariff risk assessment: ${tariffsWithRisk}/${scrapedTariffs.length} tariffs`)
            scrapedTariffs.forEach(t => {
              if (t.risk_level) {
                console.log(`   ${t.name}: ${t.risk_level} (${t.risk_score})`)
              }
            })
          } else if (riskAnalysisData.value?.risk_level) {
            console.log('🛡️ Using global risk assessment:', riskAnalysisData.value.risk_level)
          }
          
          // Fetch price forecast
          fetchPriceForecast()
          
          loading.value = false
          return
        } else {
          // Keine gescrapten Tarife verfügbar
          console.error('❌ Keine Tarife von Scrapern verfügbar')
          results.value = []
          loading.value = false
          return
        }
        
      } catch (error) {
        console.error('❌ Fehler beim Laden der Tarife:', error)
        results.value = []
      } finally {
        loading.value = false
      }
    }
    
    // Fetch price forecast from backend
    const fetchPriceForecast = async () => {
      try {
        console.log('Fetching price forecast...')
        const response = await apiService.getForecast()
        
        priceForecast.value = response.data.forecast
        console.log('Price forecast received:', response.data)
      } catch (error) {
        console.error('Error fetching price forecast:', error)
      }
    }
    
    const generateMockTariffs = () => {
      const enbwTariffs = [
        // EnBW Dynamische Tarife
        {
          id: 1,
          name: "EnBW mobility+ dynamic",
          base_price: 14.90,
          kwh_price: 0.00, // Börsenpreis + Aufschlag
          is_dynamic: true,
          price_model: "Börsenpreis + 2,0 ct/kWh Aufschlag + 14,90€/Monat Grundpreis",
          green_energy: true,
          contract_duration: 12,
          description: "Dynamischer Stromtarif mit stündlichen Börsenpreisen. Perfekt für flexible Verbraucher mit E-Auto oder Wärmepumpe.",
          app_available: true,
          price_forecast: true,
          automation_ready: true,
          avg_savings: "15-30%",
          volatility: "hoch",
          dynamic_markup: 0.02, // 2 ct/kWh Aufschlag auf Börsenpreis
          special_features: ["E-Auto Ladetarif", "Smart Home Integration", "Preisalarm"],
          features: ["dynamic", "green"]
        },
        {
          id: 2,
          name: "EnBW easy dynamic",
          base_price: 9.90,
          kwh_price: 0.00, // Börsenpreis + Aufschlag
          is_dynamic: true,
          price_model: "Börsenpreis + 3,5 ct/kWh Aufschlag + 9,90€/Monat Grundpreis",
          green_energy: true,
          contract_duration: 12,
          description: "Einfacher dynamischer Tarif für den Einstieg in variable Strompreise.",
          app_available: true,
          price_forecast: true,
          automation_ready: false,
          avg_savings: "10-25%",
          volatility: "mittel-hoch",
          dynamic_markup: 0.035, // 3,5 ct/kWh Aufschlag auf Börsenpreis
          special_features: ["Einfache App", "Tagesvorhersage"],
          features: ["dynamic", "green"]
        },
        
        // EnBW Festpreis-Tarife
        {
          id: 3,
          name: "EnBW mobility+ Zuhause",
          base_price: 14.90,
          kwh_price: 0.3280,
          is_dynamic: false,
          price_model: "Festpreis 32,80 ct/kWh + 14,90€/Monat Grundpreis",
          green_energy: true,
          contract_duration: 12,
          description: "100% Ökostrom mit E-Mobilitäts-Fokus. Ideal für E-Auto-Besitzer.",
          app_available: true,
          price_forecast: false,
          automation_ready: true,
          avg_savings: "Stabile Preise",
          volatility: "keine",
          special_features: ["E-Auto Ladetarif", "Mobility+ Vorteile", "THG-Quote möglich"],
          features: ["green"]
        },
        {
          id: 4,
          name: "EnBW easy+ Strom",
          base_price: 9.90,
          kwh_price: 0.3450,
          is_dynamic: false,
          price_model: "Festpreis 34,50 ct/kWh + 9,90€/Monat Grundpreis",
          green_energy: true,
          contract_duration: 12,
          description: "Günstiger Ökostrom-Tarif mit fairen Konditionen und kurzer Laufzeit.",
          app_available: true,
          price_forecast: false,
          automation_ready: false,
          avg_savings: "Günstig & fair",
          volatility: "keine",
          special_features: ["12 Monate Preisgarantie", "Online-Service"],
          features: ["green"]
        },
        {
          id: 5,
          name: "EnBW Basis Strom",
          base_price: 12.90,
          kwh_price: 0.3180,
          is_dynamic: false,
          price_model: "Festpreis 31,80 ct/kWh + 12,90€/Monat Grundpreis",
          green_energy: false,
          contract_duration: 24,
          description: "Klassischer Stromtarif mit bewährten Konditionen und längerer Preissicherheit.",
          app_available: false,
          price_forecast: false,
          automation_ready: false,
          avg_savings: "Bewährt & sicher",
          volatility: "keine",
          special_features: ["24 Monate Preisgarantie", "Persönlicher Service"],
          features: []
        },
        {
          id: 6,
          name: "EnBW Komfort Strom",
          base_price: 15.90,
          kwh_price: 0.2980,
          is_dynamic: false,
          price_model: "Festpreis 29,80 ct/kWh + 15,90€/Monat Grundpreis",
          green_energy: true,
          contract_duration: 24,
          description: "Premium Ökostrom-Tarif mit bestem Service und zusätzlichen Leistungen.",
          app_available: true,
          price_forecast: false,
          automation_ready: true,
          avg_savings: "Premium Service",
          volatility: "keine",
          special_features: ["24h Hotline", "Smart Home Paket", "Energieberatung"],
          features: ["green"]
        }
      ]
      
      // Filter based on user preferences
      let filteredTariffs = enbwTariffs
      
      // Removed onlyDynamic filter to show all tariffs
      
      if (formData.value.appIntegration) {
        filteredTariffs = filteredTariffs.filter(t => t.app_available)
      }
      
      // Calculate costs and add optimization potential based on flexibility
      results.value = filteredTariffs.map(tariff => {
        let baseAnnualCost
        
        if (tariff.is_dynamic) {
          // Für dynamische Tarife: Durchschnittlicher Börsenpreis (ca. 10 ct/kWh) + Aufschlag
          const avgSpotPrice = 0.10 // 10 ct/kWh durchschnittlicher Börsenpreis 2024
          const totalKwhPrice = avgSpotPrice + tariff.dynamic_markup
          baseAnnualCost = (tariff.base_price * 12) + (formData.value.annualKwh * totalKwhPrice)
        } else {
          // Für Festpreis-Tarife
          baseAnnualCost = (tariff.base_price * 12) + (formData.value.annualKwh * tariff.kwh_price)
        }
        
        // Calculate dynamic savings based on user profile
        let dynamicSavingsFactor = 1.0
        
        if (tariff.is_dynamic) {
          // Flexibility bonus
          if (formData.value.flexibility === 'high') dynamicSavingsFactor *= 0.80
          else if (formData.value.flexibility === 'medium') dynamicSavingsFactor *= 0.90
          
          // Smart home bonus
          if (formData.value.smartHome === 'advanced') dynamicSavingsFactor *= 0.85
          else if (formData.value.smartHome === 'basic') dynamicSavingsFactor *= 0.92
          
          // Time-based usage bonus (approximated)
          if (formData.value.nightUsage) dynamicSavingsFactor *= 0.88
          if (formData.value.weekendUsage) dynamicSavingsFactor *= 0.95
        }
        
        const optimizedAnnualCost = baseAnnualCost * dynamicSavingsFactor
        const monthly_cost = optimizedAnnualCost / 12
        
        // Für dynamische Tarife: zeige durchschnittlichen kWh-Preis
        const displayKwhPrice = tariff.is_dynamic ? 
          (0.10 + tariff.dynamic_markup) : tariff.kwh_price
        
        return {
          ...tariff,
          kwh_price: displayKwhPrice,
          annual_cost: Math.round(optimizedAnnualCost * 100) / 100,
          base_annual_cost: Math.round(baseAnnualCost * 100) / 100,
          monthly_cost: Math.round(monthly_cost * 100) / 100,
          potential_savings: Math.round((baseAnnualCost - optimizedAnnualCost) * 100) / 100,
          savings_vs_current: formData.value.currentCost ? 
            Math.max(0, (formData.value.currentCost * 12) - optimizedAnnualCost) : 0,
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
      selectedTariff.value = tariff
      showDetailsModal.value = true
      // Fetch risk analysis data when modal opens
      fetchRiskAnalysis()
    }
    
    const closeDetailsModal = () => {
      showDetailsModal.value = false
      selectedTariff.value = null
    }
    
    const scrollToRiskBreakdown = () => {
      const element = document.getElementById('risk-breakdown')
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
    
    const fetchRiskAnalysis = async () => {
      // Only fetch if we have uploaded file
      if (!uploadedFile.value) {
        console.log('No uploaded file, skipping risk analysis')
        riskAnalysisData.value = null
        return
      }
      
      console.log('Fetching risk analysis for file:', uploadedFile.value.name)
      riskAnalysisLoading.value = true
      riskAnalysisError.value = null
      
      try {
        const response = await apiService.getRiskAnalysis(uploadedFile.value, 30)
        riskAnalysisData.value = response.data
        console.log('Risk analysis data loaded:', riskAnalysisData.value)
      } catch (err) {
        console.error('Error fetching risk analysis:', err)
        riskAnalysisError.value = 'Fehler beim Laden der Risikoanalyse: ' + (err.response?.data?.detail || err.message)
      } finally {
        riskAnalysisLoading.value = false
      }
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
      
      // Validate file type - only CSV allowed
      const allowedTypes = ['text/csv']
      const allowedExtensions = ['.csv']
      
      const hasValidType = allowedTypes.includes(file.type) || 
                          allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
      
      if (!hasValidType) {
        fileError.value = 'Bitte wählen Sie eine CSV-Datei (.csv)'
        return
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        fileError.value = 'Die Datei ist zu groß. Maximale Größe: 5MB'
        return
      }
      
      uploadedFile.value = file
      
      try {
        await parseCSV(file)
      } catch (error) {
        console.error('Error parsing file:', error)
        fileError.value = 'Fehler beim Verarbeiten der CSV-Datei. Bitte überprüfen Sie das Format.'
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
    
    // Helper functions for forecast display
    const getDayName = (dayName) => {
      const dayNames = {
        'Monday': 'Mo',
        'Tuesday': 'Di', 
        'Wednesday': 'Mi',
        'Thursday': 'Do',
        'Friday': 'Fr',
        'Saturday': 'Sa',
        'Sunday': 'So'
      }
      return dayNames[dayName] || dayName.substring(0, 2)
    }
    
    const getPriceBarWidth = (day) => {
      // Calculate width based on price range (0-40ct)
      const maxPrice = Math.min(day.max_price * 100, 40)
      return (maxPrice / 40) * 100
    }
    
    // Translate technical feature keys to German user-friendly descriptions
    const translateFeature = (feature) => {
      const featureMap = {
        'dynamic': 'Dynamischer Tarif',
        'real-time-pricing': 'Echtzeitpreise',
        'smart-meter-required': 'Smart Meter erforderlich',
        'green': '100% Ökostrom',
        'renewable-energy': '100% Ökostrom',
        'fixed': 'Fester Tarif',
        'fixed-rate': 'Fester Tarif',
        'app': 'Appsteuerung',
        'app-available': 'Mobile App verfügbar',
        'automation': 'Automatisierung möglich',
        'price-guarantee': 'Preisgarantie',
        'no-cancellation-fee': 'Keine Kündigungsgebühr',
        'online-service': 'Online-Kundenservice'
      }
      return featureMap[feature] || feature
    }
    
    // Get provider description based on provider name
    const getProviderDescription = (providerName) => {
      const descriptions = {
        'Tado': 'tado° ist primär ein Smart-Home-Anbieter für intelligente Heizungssteuerung und bietet in Kooperation mit Energieversorgern dynamische Stromtarife an. Das Unternehmen verbindet smarte Thermostate mit flexiblen Energietarifen für optimierte Energiekosten.',
        'EnBW': 'EnBW ist einer der größten Energieversorger Deutschlands und bietet bundesweit Ökostrom sowie Gas aus konventionellen und erneuerbaren Quellen. Das Unternehmen betreibt ein großes Ladenetz für Elektrofahrzeuge und investiert stark in erneuerbare Energien.',
        'Tibber': 'Tibber ist ein digitaler Stromanbieter, der Strom zum Einkaufspreis ohne Aufschlag weitergibt und sich über eine monatliche Gebühr finanziert. Die App ermöglicht stundenbasierte Strompreise und intelligente Steuerung von Haushaltsgeräten für maximale Kostenersparnis.'
      }
      return descriptions[providerName] || 'Einer der führenden Energieversorger in Deutschland.'
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
      priceForecast,
      riskAnalysisData,
      riskAnalysisLoading,
      riskAnalysisError,
      showDetailsModal,
      selectedTariff,
      calculateTariffs,
      sortResults,
      selectTariff,
      showTariffDetails,
      closeDetailsModal,
      scrollToRiskBreakdown,
      fetchRiskAnalysis,
      handleFileSelect,
      handleFileDrop,
      removeFile,
      formatFileSize,
      updateConsumptionFromHousehold,
      getDayName,
      getPriceBarWidth,
      translateFeature,
      getProviderDescription
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

.monthly-cost-main {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.annual-cost-small {
  color: #6b7280;
  font-size: 0.9rem;
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
  background: #e0e7ff;
  color: #4338ca;
}

.badge-tech {
  background: #ede9fe;
  color: #7c3aed;
}

.badge-smart {
  background: #ccfbf1;
  color: #0f766e;
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

.special-features {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.special-features h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.special-features ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.special-features li {
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

.text-red-600 {
  color: #dc2626;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* API Status Indicator */
.api-status {
  margin: 1rem 0;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-indicator.success {
  background-color: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #22c55e;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Forecast Section Styles */
.forecast-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.forecast-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  margin-top: 1rem;
}

.forecast-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.forecast-card-full {
  width: 100%;
}

.forecast-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
}

.forecast-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.forecast-content {
  padding: 1.5rem;
}

/* Savings Prediction Styles */
.prediction-result {
  text-align: center;
}

.prediction-main {
  margin-bottom: 1rem;
}

.prediction-percentage {
  font-size: 2.5rem;
  font-weight: 700;
  color: #059669;
  display: block;
}

.prediction-label {
  font-size: 0.9rem;
  color: #6b7280;
  font-weight: 500;
}

.prediction-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
}

.prediction-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.prediction-item .label {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.prediction-item .value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #059669;
}

.prediction-recommendations {
  margin-top: 1rem;
  text-align: left;
}

.prediction-recommendations h5 {
  font-size: 0.9rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.prediction-recommendations ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.prediction-recommendations li {
  font-size: 0.85rem;
  color: #6b7280;
  padding: 0.25rem 0;
  display: flex;
  align-items: start;
  gap: 0.5rem;
}

.prediction-recommendations li:before {
  content: "→";
  color: #059669;
  font-weight: 600;
}

/* Price Forecast Styles */
.price-forecast {
  text-align: center;
}

.forecast-chart {
  margin-bottom: 1rem;
}

.day-forecast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.day-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  min-width: 25px;
}

.price-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.min-price, .max-price {
  font-size: 0.75rem;
  color: #6b7280;
  min-width: 40px;
  font-weight: 500;
}

.price-avg {
  font-size: 0.75rem;
  color: #059669;
  min-width: 45px;
  font-weight: 600;
  text-align: right;
}

.price-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.price-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.forecast-summary {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.forecast-summary p {
  margin: 0.25rem 0;
  font-size: 0.85rem;
  color: #0369a1;
}

.loading-prediction, .loading-forecast {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.9rem;
  padding: 2rem 0;
}

/* Enhanced Tariff Info Styles */

.cost-breakdown {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #3b82f6;
}

.cost-breakdown h4 {
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.breakdown-grid {
  display: grid;
  gap: 0.5rem;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.breakdown-item:last-child {
  border-bottom: none;
}

.breakdown-item.highlight {
  background: #ecfdf5;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #10b981;
  margin-top: 0.5rem;
}

.breakdown-label {
  font-size: 0.9rem;
  color: #6b7280;
}

.breakdown-value {
  font-weight: 600;
  color: #1f2937;
}

.breakdown-value.savings {
  color: #10b981;
  font-weight: 700;
}

.best-deal-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, #fef3c7, #fbbf24);
  border-radius: 8px;
  border: 2px solid #f59e0b;
}

.best-deal-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #92400e;
  justify-content: center;
}

.best-deal-badge i {
  color: #f59e0b;
}

.optimization-savings {
  margin-top: 1rem;
  padding: 1rem;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-radius: 8px;
  border-left: 4px solid #3b82f6;
}

.optimization-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 0.75rem;
}

.optimization-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.optimization-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #1e3a8a;
}

.optimization-item i {
  color: #3b82f6;
  width: 16px;
}

.current-savings {
  margin-top: 1rem;
  padding: 1rem;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border-radius: 8px;
  border-left: 4px solid #10b981;
  text-align: center;
}

.savings-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #065f46;
  margin-bottom: 0.5rem;
}

.savings-amount-large {
  font-size: 1.5rem;
  font-weight: 700;
  color: #059669;
  margin-bottom: 0.25rem;
}

.savings-breakdown-small {
  font-size: 0.85rem;
  color: #047857;
  margin-bottom: 0.5rem;
}

.savings-percentage {
  font-size: 0.9rem;
  font-weight: 600;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 20px;
  padding: 0.25rem 0.75rem;
  display: inline-block;
}



/* Responsive Forecast Cards */
@media (max-width: 768px) {
  .forecast-cards {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .prediction-details {
    grid-template-columns: 1fr;
  }
  
  .breakdown-grid {
    font-size: 0.85rem;
  }
  
  .best-deal-info {
    padding: 0.75rem;
  }
  
  .savings-summary {
    font-size: 0.85rem;
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 1200px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.modal-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 2rem;
}

.tariff-overview {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2rem;
  align-items: center;
}

.overview-item h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.tariff-type {
  margin: 0 0 0.75rem 0;
}

.overview-item .tariff-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: nowrap;
  overflow-x: auto;
  margin-top: 0.5rem;
  padding-bottom: 0.25rem;
}

.cost-display {
  text-align: right;
}

.monthly-cost {
  font-size: 2rem;
  font-weight: 700;
  color: #059669;
  line-height: 1;
}

.cost-label {
  font-size: 0.9rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.modal-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.detail-section, .cost-section, .contract-section {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
}

.detail-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-list {
  margin-bottom: 1.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  font-weight: 500;
  color: #6b7280;
}

.detail-row .value {
  font-weight: 600;
  color: #1f2937;
}

.detail-row .value.highlight {
  color: #059669;
  font-size: 1.1rem;
}

.features-list h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.features-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  color: #4b5563;
  position: relative;
}

.features-list li .risk-info-button {
  margin-left: auto;
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.features-list li .risk-info-button:hover {
  background: #eff6ff;
  color: #1d4ed8;
  transform: scale(1.1);
}

.features-list li .risk-info-button:active {
  transform: scale(0.95);
}

.features-list li i {
  color: #059669;
  font-size: 0.9rem;
}

.features-list li.risk-info-low {
  background: #f0fdf4;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid #10b981;
  margin-top: 0.5rem;
}

.features-list li.risk-info-low i {
  color: #10b981;
}

.features-list li.risk-info-moderate {
  background: #fffbeb;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid #f59e0b;
  margin-top: 0.5rem;
}

.features-list li.risk-info-moderate i {
  color: #f59e0b;
}

.features-list li.risk-info-high {
  background: #fef2f2;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid #ef4444;
  margin-top: 0.5rem;
}

.features-list li.risk-info-high i {
  color: #ef4444;
}

.detail-row.highlight-row {
  background: #f0f9ff;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #0ea5e9;
  margin-top: 0.5rem;
}

/* Cost Section Styles */
.cost-breakdown-detail {
  margin-bottom: 1.5rem;
}

.cost-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 1rem;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.cost-item.total {
  border-top: 2px solid #3b82f6;
  border-bottom: none;
  font-weight: 700;
  background: #f0f9ff;
  padding: 1rem;
  border-radius: 6px;
  margin-top: 0.5rem;
}

.cost-label {
  font-size: 0.9rem;
  color: #4b5563;
}

.cost-value {
  font-weight: 600;
  color: #1f2937;
}

.cost-percentage {
  font-size: 0.8rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.cost-separator {
  height: 1px;
  background: #d1d5db;
  margin: 0.5rem 0;
  grid-column: 1 / -1;
}

.cost-comparison {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.cost-comparison h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.comparison-item:last-child {
  border-bottom: none;
}

.comparison-label {
  font-size: 0.85rem;
  color: #6b7280;
}

.comparison-value {
  font-weight: 600;
  color: #059669;
}

.optimization-potential h4 {
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.optimization-stats {
  display: grid;
  gap: 0.75rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #ffffff;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.stat-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.85rem;
}

.stat-content {
  flex: 1;
}

.stat-title {
  font-size: 0.85rem;
  color: #4b5563;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-weight: 700;
  color: #059669;
  font-size: 0.9rem;
}

/* Contract Section Styles */
.contract-details {
  margin-bottom: 1.5rem;
}

.contract-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.contract-item:last-child {
  border-bottom: none;
}

.contract-item > i {
  color: #3b82f6;
  margin-top: 0.25rem;
  width: 16px;
}

.contract-content {
  flex: 1;
}

.contract-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.contract-value {
  color: #4b5563;
  font-size: 0.85rem;
  line-height: 1.4;
}

.provider-info {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
}

.provider-info h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.provider-details {
  display: flex;
  gap: 0.75rem;
}

.provider-logo {
  width: 50px;
  height: 50px;
  flex-shrink: 0;
}

.logo-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.7rem;
  text-align: center;
}

.provider-content {
  flex: 1;
}

.provider-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.provider-description {
  color: #4b5563;
  font-size: 0.8rem;
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.provider-rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: nowrap;
}

.rating-stars {
  color: #f59e0b;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.1rem;
  white-space: nowrap;
  flex-shrink: 0;
}

.rating-text {
  color: #6b7280;
  font-size: 0.8rem;
  white-space: nowrap;
}

/* Charts Container Styles */
.charts-container {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.charts-title {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
  justify-content: center;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

.chart-container {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  min-height: 300px;
}

.chart-title {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
  justify-content: center;
}

.chart-placeholder {
  height: 240px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 0.9rem;
  text-align: center;
  padding: 2rem;
  border: 2px dashed #cbd5e1;
}

.chart-placeholder i {
  display: block;
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: #94a3b8;
}

.chart-description {
  margin-top: 1rem;
  font-size: 0.8rem;
  color: #6b7280;
  text-align: center;
  line-height: 1.4;
}

/* Responsive Design for Charts */
@media (max-width: 768px) {
  .modal-info-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .chart-container {
    padding: 1rem;
    min-height: 250px;
  }
  
  .chart-placeholder {
    height: 200px;
    padding: 1.5rem;
  }
  
  .modal-content {
    max-width: 95vw;
    margin: 1rem;
  }
  
  .modal-title {
    font-size: 1.25rem;
  }
  
  .cost-item {
    grid-template-columns: 1fr auto;
    gap: 0.5rem;
  }
  
  .cost-percentage {
    display: none;
  }
  
  .provider-details {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .provider-logo {
    align-self: flex-start;
  }
}

/* Animation Improvements */
.modal-content {
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.tariff-card {
  transition: all 0.3s ease;
}

.tariff-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.cost-item {
  transition: background-color 0.2s ease;
}

.cost-item:hover {
  background-color: #f9fafb;
}

.stat-item {
  transition: all 0.2s ease;
}

.stat-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart-placeholder {
  transition: all 0.3s ease;
}

.chart-placeholder:hover {
  background: linear-gradient(135deg, #f1f5f9 0%, #d1d9e6 100%);
  border-color: #94a3b8;
}

.chart-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
}

.chart-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-placeholder {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.placeholder-content > i {
  font-size: 3rem;
  color: #9ca3af;
}

.placeholder-content h4 {
  margin: 0;
  font-size: 1.1rem;
  color: #4b5563;
}

.placeholder-content p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.placeholder-data {
  margin-top: 1rem;
  width: 100%;
}

.mock-chart-bars {
  display: flex;
  align-items: end;
  justify-content: center;
  gap: 0.5rem;
  height: 80px;
  margin-bottom: 1rem;
}

.bar {
  width: 20px;
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 2px 2px 0 0;
  min-height: 20px;
}

.mock-pie-chart {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  margin: 0 auto 1rem auto;
  position: relative;
  background: conic-gradient(
    from 0deg,
    #ef4444 0deg 120deg,
    #f59e0b 120deg 240deg,
    #10b981 240deg 360deg
  );
}

.savings-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
  font-size: 0.85rem;
}

.savings-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.savings-1 { background-color: #ef4444; }
.savings-2 { background-color: #f59e0b; }
.savings-3 { background-color: #10b981; }

.placeholder-data small {
  color: #9ca3af;
  font-size: 0.8rem;
  font-style: italic;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

/* Risk Analysis Styles */
.risk-analysis-container {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e5e7eb;
}

.risk-analysis-container .loading-state,
.risk-analysis-container .error-state,
.risk-analysis-container .no-data-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px dashed #d1d5db;
}

.risk-analysis-container .loading-state i {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #3b82f6;
}

.risk-analysis-container .error-state {
  color: #ef4444;
  background: #fef2f2;
  border-color: #fca5a5;
}

.risk-analysis-container .error-state i {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.risk-analysis-container .no-data-state i {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #9ca3af;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-title i {
  color: #3b82f6;
}

.risk-analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.chart-card {
  grid-column: 1 / -1;
}

.risk-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;
}

.risk-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.risk-card-header {
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.risk-card-header h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.risk-card-header i {
  color: #3b82f6;
}

.risk-card-body {
  padding: 1.5rem;
}

.risk-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.risk-metric:last-of-type {
  border-bottom: none;
}

.risk-metric.highlight {
  background: #f9fafb;
  padding: 1rem;
  margin: 0.5rem -0.5rem;
  border-radius: 8px;
  border: none;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 1rem;
  color: #1f2937;
  font-weight: 600;
}

.text-success {
  color: #10b981 !important;
}

.text-danger {
  color: #ef4444 !important;
}

.risk-badge {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

.badge-danger {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.coincidence-metric {
  display: flex;
  justify-content: center;
  padding: 1rem 0;
}

.coincidence-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid;
  margin-bottom: 1rem;
}

.circle-success {
  border-color: #10b981;
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
}

.circle-warning {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
}

.circle-danger {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fee2e2, #fecaca);
}

.circle-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
}

.circle-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 0.25rem;
}

.badge-fixed {
  background: #9ca3af;
  color: white;
}

/* Compact Risk Analysis Content */
.risk-analysis-content {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.fixed-tariff-note {
  padding: 1rem;
}

.info-banner {
  background: linear-gradient(135deg, #dbeafe, #e0f2fe);
  border: 1px solid #3b82f6;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.info-banner i {
  color: #3b82f6;
  font-size: 1.25rem;
  margin-top: 0.125rem;
  flex-shrink: 0;
}

.info-banner p {
  margin: 0;
  color: #1e3a8a;
  font-size: 0.9rem;
  line-height: 1.5;
}

.risk-summary-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.risk-summary-header {
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.risk-summary-header i {
  color: #000000;
}

.risk-summary-body {
  padding: 1rem;
}

.risk-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 0.875rem;
}

.risk-stat:not(:last-child) {
  border-bottom: 1px solid #f3f4f6;
}

.risk-stat.highlight {
  background: #f9fafb;
  padding: 0.75rem;
  margin: 0.5rem -1rem;
  border-bottom: none;
}

.stat-label {
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  color: #1f2937;
  font-weight: 600;
}

.coincidence-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.coincidence-circle-small {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid;
  flex-shrink: 0;
}

.coincidence-circle-small .circle-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.coincidence-circle-small.circle-success {
  border-color: #047857;
}

.coincidence-circle-small.circle-success .circle-value {
  color: #047857;
}

.coincidence-circle-small.circle-warning {
  border-color: #d97706;
}

.coincidence-circle-small.circle-warning .circle-value {
  color: #d97706;
}

.coincidence-circle-small.circle-danger {
  border-color: #dc2626;
}

.coincidence-circle-small.circle-danger .circle-value {
  color: #dc2626;
}

.coincidence-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-text {
  font-size: 0.875rem;
  color: #4b5563;
}

.info-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  align-self: flex-start;
}

.risk-chart-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.risk-chart-body {
  padding: 1rem;
}

/* Detailed Risk Breakdown Section */
.risk-breakdown-section {
  margin-top: 2rem;
  padding: 2rem;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.risk-breakdown-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.risk-breakdown-title i {
  color: #3b82f6;
}

.risk-overview-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.risk-score-display {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.risk-score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 6px solid;
  flex-shrink: 0;
}

.risk-score-circle.score-low {
  border-color: #10b981;
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
}

.risk-score-circle.score-moderate {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
}

.risk-score-circle.score-high {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fee2e2, #fecaca);
}

.score-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.score-label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.risk-score-info {
  flex: 1;
}

.risk-level-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.risk-message {
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.risk-factors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.risk-factor-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  border-left: 4px solid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.risk-factor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.risk-factor-card.factor-positive {
  border-left-color: #10b981;
  background: linear-gradient(to right, #f0fdf4 0%, white 100%);
}

.risk-factor-card.factor-neutral {
  border-left-color: #6b7280;
  background: linear-gradient(to right, #f9fafb 0%, white 100%);
}

.risk-factor-card.factor-negative {
  border-left-color: #ef4444;
  background: linear-gradient(to right, #fef2f2 0%, white 100%);
}

.factor-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.factor-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
}

.factor-positive .factor-icon {
  background: #d1fae5;
  color: #059669;
}

.factor-neutral .factor-icon {
  background: #f3f4f6;
  color: #6b7280;
}

.factor-negative .factor-icon {
  background: #fee2e2;
  color: #dc2626;
}

.factor-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.factor-detail {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}

.factor-impact-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.factor-positive .factor-impact-label {
  color: #059669;
}

.factor-neutral .factor-impact-label {
  color: #6b7280;
}

.factor-negative .factor-impact-label {
  color: #dc2626;
}

/* Responsive Modal */
@media (max-width: 1024px) {
  .modal-grid {
    grid-template-columns: 1fr;
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 1rem;
  }
  
  .cost-display {
    text-align: center;
  }
  
  .risk-analysis-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .modal-content {
    margin: 0;
    border-radius: 0;
    max-height: 100vh;
  }
  
  .modal-header {
    border-radius: 0;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .modal-actions .btn {
    width: 100%;
  }
  
  .risk-score-display {
    flex-direction: column;
    text-align: center;
  }
  
  .risk-factors-grid {
    grid-template-columns: 1fr;
  }
  
  .risk-breakdown-section {
    padding: 1rem;
  }
}
</style>
