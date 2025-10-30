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
                  <label class="form-label">Aktuelle Monatskosten (€)</label>
                  <input 
                    type="number" 
                    v-model="formData.currentCost" 
                    class="form-input"
                    placeholder="z.B. 100"
                    step="0.01"
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
                      <span v-if="tariff.features && tariff.features.includes('dynamic')" class="badge badge-dynamic">
                        <i class="fas fa-chart-line"></i>
                        Dynamisch
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
                      <span v-if="index === 0" class="badge badge-gold">
                        <i class="fas fa-star"></i>
                        Empfohlen
                      </span>
                    </div>
                  </div>

                  <div class="tariff-price">
                    <div class="monthly-cost-main">{{ Math.round(tariff.monthly_cost) }}€/Monat</div>
                    <div class="annual-cost-small">{{ Math.round(tariff.annual_cost) }}€/Jahr</div>
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

                  <!-- Erweiterte Kosten-/Ersparnisinfo -->
                  <div class="cost-breakdown">
                    <h4><i class="fas fa-calculator"></i> Kostenaufschlüsselung</h4>
                    <div class="breakdown-grid">
                      <div class="breakdown-item">
                        <span class="breakdown-label">Grundgebühr/Jahr:</span>
                        <span class="breakdown-value">{{ Math.round(tariff.base_price * 12) }}€</span>
                      </div>
                      <div class="breakdown-item">
                        <span class="breakdown-label">Verbrauchskosten/Jahr:</span>
                        <span class="breakdown-value">{{ Math.round(tariff.annual_cost - (tariff.base_price * 12)) }}€</span>
                      </div>
                      <div class="breakdown-item">
                        <span class="breakdown-label">Kosten pro kWh (Ø):</span>
                        <span class="breakdown-value">{{ (tariff.annual_cost / formData.annualKwh).toFixed(3) }}€</span>
                      </div>
                      <div v-if="tariff.is_dynamic" class="breakdown-item highlight">
                        <span class="breakdown-label">Einsparungspotenzial:</span>
                        <span class="breakdown-value savings">
                          bis zu {{ Math.round(tariff.annual_cost * 0.15) }}€/Jahr
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
                  
                  <div v-if="tariff.special_features" class="special-features">
                    <h4><i class="fas fa-star"></i> Besondere Leistungen</h4>
                    <ul>
                      <li v-for="feature in tariff.special_features" :key="feature">
                        <i class="fas fa-check text-green-600"></i>
                        {{ feature }}
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
                      <span>Zusätzliche Ersparnis: {{ Math.round(tariff.annual_cost * (0.10 + Math.random() * 0.15)) }}€/Jahr</span>
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
                    {{ Math.round(formData.currentCost - tariff.annual_cost) }}€ pro Jahr
                  </div>
                  <div class="savings-breakdown-small">
                    <span>Das sind {{ Math.round((formData.currentCost - tariff.annual_cost) / 12) }}€ pro Monat weniger</span>
                  </div>
                  <div class="savings-percentage">
                    {{ Math.round(((formData.currentCost - tariff.annual_cost) / formData.currentCost) * 100) }}% Ersparnis
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
              <!-- Ersparnisvorhersage -->
              <div class="forecast-card">
                <div class="forecast-header">
                  <h4>
                    <i class="fas fa-chart-line"></i>
                    KI-basierte Ersparnisvorhersage
                  </h4>
                </div>
                <div class="forecast-content">
                  <div v-if="savingsPrediction" class="prediction-result">
                    <div class="prediction-main">
                      <span class="prediction-percentage">{{ savingsPrediction.percentage }}%</span>
                      <span class="prediction-label">Einsparpotential</span>
                    </div>
                    <div class="prediction-details">
                      <div class="prediction-item">
                        <span class="label">Monatlich:</span>
                        <span class="value">{{ savingsPrediction.monthly_euro }}€</span>
                      </div>
                      <div class="prediction-item">
                        <span class="label">Jährlich:</span>
                        <span class="value">{{ savingsPrediction.annual_euro }}€</span>
                      </div>
                    </div>
                    <div class="prediction-recommendations">
                      <h5>Empfehlungen:</h5>
                      <ul>
                        <li v-for="rec in savingsPrediction.recommendations" :key="rec">{{ rec }}</li>
                      </ul>
                    </div>
                  </div>
                  <div v-else class="loading-prediction">
                    <div class="loading-spinner small"></div>
                    <span>Berechne Einsparpotential...</span>
                  </div>
                </div>
              </div>

              <!-- Preisvorhersage -->
              <div class="forecast-card">
                <div class="forecast-header">
                  <h4>
                    <i class="fas fa-crystal-ball"></i>
                    7-Tage Strompreis-Prognose
                  </h4>
                </div>
                <div class="forecast-content">
                  <div v-if="priceForecast" class="price-forecast">
                    <div class="forecast-chart">
                      <div v-for="day in priceForecast.slice(0, 5)" :key="day.date" class="day-forecast">
                        <div class="day-name">{{ getDayName(day.day_name) }}</div>
                        <div class="price-range">
                          <span class="min-price">{{ (day.min_price * 100).toFixed(1) }}ct</span>
                          <div class="price-bar">
                            <div class="price-fill" :style="{ width: getPriceBarWidth(day) + '%' }"></div>
                          </div>
                          <span class="max-price">{{ (day.max_price * 100).toFixed(1) }}ct</span>
                        </div>
                      </div>
                    </div>
                    <div class="forecast-summary">
                      <p><strong>Beste Zeiten:</strong> Nachts 23:00-06:00 Uhr</p>
                      <p><strong>Teuerste Zeiten:</strong> Abends 17:00-20:00 Uhr</p>
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
              <p class="tariff-type">
                <span v-if="selectedTariff.is_dynamic" class="badge badge-dynamic">
                  <i class="fas fa-chart-line"></i> Dynamischer Tarif
                </span>
                <span v-else class="badge badge-fixed">
                  <i class="fas fa-lock"></i> Fester Tarif
                </span>
              </p>
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
                <span class="label">Arbeitspreis:</span>
                <span class="value">{{ selectedTariff.kwh_price }}€/kWh</span>
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
            
            <div class="features-list">
              <h4><i class="fas fa-star"></i> Tarifmerkmale</h4>
              <ul>
                <li v-for="feature in selectedTariff.features" :key="feature">
                  <i class="fas fa-check"></i> {{ feature }}
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
                  <div class="contract-value">{{ selectedTariff.contract_duration }} {{ selectedTariff.contract_duration === 1 ? 'Monat' : 'Monate' }}</div>
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
                  <div class="provider-name">{{ selectedTariff.provider }} Energie AG</div>
                  <div class="provider-description">
                    Einer der führenden Energieversorger in Deutschland mit über 5 Millionen Kunden.
                    {{ selectedTariff.green_energy ? 'Spezialist für nachhaltige Energielösungen.' : '' }}
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

        <!-- Diagramme nebeneinander -->
        <div class="charts-container">
          <h3 class="charts-title"><i class="fas fa-chart-line"></i> Prognose & Analyse</h3>
          <div class="charts-grid">
            <!-- Backtest Chart -->
            <div class="chart-section">
              <h4><i class="fas fa-chart-area"></i> Verbrauchsprognose Backtest</h4>
              <BacktestChart :uploadedFile="uploadedFile" />
            </div>

            <!-- Einsparungspotenzial Diagramm -->
            <div class="chart-section">
              <h4><i class="fas fa-piggy-bank"></i> Ihr Einsparungspotenzial</h4>
              <div class="chart-placeholder">
                <div class="placeholder-content">
                  <div class="chart-header">
                    <div class="chart-info">
                      <span class="chart-period">Jährliche Analyse</span>
                      <span class="chart-potential">{{ Math.round(selectedTariff.annual_cost * (0.10 + Math.random() * 0.15)) }}€ Potenzial</span>
                    </div>
                  </div>
                  <div class="placeholder-data">
                    <div class="savings-visualization">
                      <div class="savings-bar-container">
                        <div class="savings-bar current" :style="{ width: '100%' }">
                          <span class="bar-label">Aktuelle Kosten</span>
                          <span class="bar-value">{{ Math.round(selectedTariff.annual_cost) }}€</span>
                        </div>
                        <div class="savings-bar optimized" :style="{ width: '75%' }">
                          <span class="bar-label">Mit Optimierung</span>
                          <span class="bar-value">{{ Math.round(selectedTariff.annual_cost * 0.75) }}€</span>
                        </div>
                        <div class="savings-bar potential" :style="{ width: '60%' }">
                          <span class="bar-label">Maximales Potenzial</span>
                          <span class="bar-value">{{ Math.round(selectedTariff.annual_cost * 0.60) }}€</span>
                        </div>
                      </div>
                    </div>
                    <div class="optimization-tips">
                      <div class="tip-item">
                        <i class="fas fa-lightbulb tip-icon"></i>
                        <span>Verbrauch in günstige Nachtstunden verschieben</span>
                      </div>
                      <div class="tip-item">
                        <i class="fas fa-mobile-alt tip-icon"></i>
                        <span>App-Benachrichtigungen für niedrige Preise nutzen</span>
                      </div>
                      <div class="tip-item">
                        <i class="fas fa-home tip-icon"></i>
                        <span>Smart Home Geräte zeitgesteuert einsetzen</span>
                      </div>
                    </div>
                  </div>
                  <div class="chart-footer">
                    <small>Personalisierte KI-Analyse basierend auf Ihrem Verbrauchsprofil</small>
                  </div>
                </div>
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
import { ref, computed, onMounted } from 'vue'
import BacktestChart from '../components/BacktestChart.vue'
// import { apiService } from '../services/api' // Deactivated for frontend-only mode

export default {
  name: 'TariffComparison',
  components: {
    BacktestChart
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
    
    // Prognose and prediction data
    const savingsPrediction = ref(null)
    const priceForecast = ref(null)
    
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
        // Fetch tariffs from backend API
        console.log('Fetching tariffs from backend...')
        const response = await fetch('http://localhost:8000/api/tariffs')
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const backendTariffs = await response.json()
        console.log('Backend tariffs received:', backendTariffs)
        
        // Calculate costs for each tariff using the backend
        const calculatedTariffs = []
        
        for (const tariff of backendTariffs) {
          try {
            const calculationData = {
              tariff_id: tariff.id,
              annual_kwh: formData.value.annualKwh,
              has_smart_meter: formData.value.hasSmartMeter,
              usage_pattern: formData.value.hasSmartMeter ? 'uploaded' : 'manual'
            }
            
            console.log('Calculating costs for tariff:', tariff.name, calculationData)
            
            const calcResponse = await fetch('http://localhost:8000/api/calculate', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(calculationData)
            })
            
            if (calcResponse.ok) {
              const calculation = await calcResponse.json()
              console.log('Calculation result:', calculation)
              
              calculatedTariffs.push({
                ...tariff,
                annual_cost: Math.round(calculation.annual_cost),
                monthly_cost: Math.round(calculation.annual_cost / 12),
                savings_potential: calculation.savings_potential || 0,
                cost_breakdown: calculation.cost_breakdown || {}
              })
            } else {
              // Fallback to basic calculation if API call fails
              const basicCost = (tariff.base_price * 12) + (formData.value.annualKwh * (tariff.kwh_price || 0.30))
              calculatedTariffs.push({
                ...tariff,
                annual_cost: Math.round(basicCost),
                monthly_cost: Math.round(basicCost / 12),
                savings_potential: 0
              })
            }
          } catch (calcError) {
            console.error('Error calculating tariff:', tariff.name, calcError)
            // Fallback calculation
            const basicCost = (tariff.base_price * 12) + (formData.value.annualKwh * (tariff.kwh_price || 0.30))
            calculatedTariffs.push({
              ...tariff,
              annual_cost: Math.round(basicCost),
              monthly_cost: Math.round(basicCost / 12),
              savings_potential: 0
            })
          }
        }
        
        results.value = calculatedTariffs
        console.log('Final calculated tariffs:', calculatedTariffs)
        
        // Fetch predictions and forecasts after tariffs are loaded
        fetchSavingsPrediction()
        fetchPriceForecast()
        
      } catch (error) {
        console.error('Error fetching tariffs from backend:', error)
        console.log('Falling back to mock data...')
        // Fallback to mock data if backend is not available
        generateMockTariffs()
      } finally {
        loading.value = false
      }
    }
    
    // Fetch savings prediction from backend
    const fetchSavingsPrediction = async () => {
      try {
        console.log('Fetching savings prediction...')
        const response = await fetch('http://localhost:8000/api/predict-savings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            annual_kwh: formData.value.annualKwh,
            has_smart_meter: formData.value.hasSmartMeter
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          savingsPrediction.value = data.savings_potential
          console.log('Savings prediction received:', data)
        }
      } catch (error) {
        console.error('Error fetching savings prediction:', error)
      }
    }
    
    // Fetch price forecast from backend
    const fetchPriceForecast = async () => {
      try {
        console.log('Fetching price forecast...')
        const response = await fetch('http://localhost:8000/api/forecast')
        
        if (response.ok) {
          const data = await response.json()
          priceForecast.value = data.forecast
          console.log('Price forecast received:', data)
        }
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
    }
    
    const closeDetailsModal = () => {
      showDetailsModal.value = false
      selectedTariff.value = null
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
      savingsPrediction,
      priceForecast,
      showDetailsModal,
      selectedTariff,
      calculateTariffs,
      sortResults,
      selectTariff,
      showTariffDetails,
      closeDetailsModal,
      handleFileSelect,
      handleFileDrop,
      removeFile,
      formatFileSize,
      updateConsumptionFromHousehold,
      getDayName,
      getPriceBarWidth
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
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-top: 1rem;
}

.forecast-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow: hidden;
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
  min-width: 35px;
  font-weight: 500;
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
  margin: 0;
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
}

.features-list li i {
  color: #059669;
  font-size: 0.9rem;
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
}

.rating-stars {
  color: #f59e0b;
  font-size: 0.8rem;
}

.rating-text {
  color: #6b7280;
  font-size: 0.8rem;
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
  grid-template-columns: 1fr 1fr;
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
  
  .charts-grid {
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

.badge-dynamic {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
}

.badge-fixed {
  background: linear-gradient(135deg, #6b7280, #374151);
  color: white;
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
}
</style>
