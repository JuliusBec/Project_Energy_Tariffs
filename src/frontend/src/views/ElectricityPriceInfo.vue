<template>
  <div class="electricity-price-info">
    <!-- Header Section -->
    <div class="hero-section">
      <div class="container">
        <h1 class="page-title">
          <i class="fas fa-chart-pie"></i>
          Wie setzen sich Strompreise zusammen?
        </h1>
        <p class="page-subtitle">
          Verstehen Sie die verschiedenen Komponenten Ihres Strompreises und warum ein Vergleich sich lohnt.
        </p>
      </div>
    </div>

    <div class="container">
      <!-- Price Basics -->
      <section class="price-basics">
        <h2 class="section-title">
          <i class="fas fa-info-circle"></i>
          Grundlagen der Energiepreise
        </h2>
        
        <div class="basics-grid">
          <div class="basic-card" :class="{ 'expanded': arbeitspreisExpanded }" @click="toggleArbeitspreis">
            <div class="basic-header">
              <h3>
                <i class="fas fa-zap"></i>
                Arbeitspreis (Energie)
              </h3>
              <i class="fas fa-chevron-down toggle-icon" :class="{ 'rotated': arbeitspreisExpanded }"></i>
            </div>
            <div class="basic-content" v-show="arbeitspreisExpanded">
              <p class="basic-intro">Die wichtigste Größe für die Höhe der Strom- oder Gasrechnung ist in der Regel der sogenannte Arbeitspreis:</p>
              <ul class="basic-points">
                <li>Dieser wird in Cent pro Kilowattstunde (ct/kWh) angegeben.</li>
                <li>Je mehr Kilowattstunden Sie verbrauchen, desto höher fällt Ihre Jahresrechnung aus.</li>
                <li>Der Arbeitspreis multipliziert mit Ihrem Jahresverbrauch wird zum Grundpreis addiert und ergibt so Ihren Abrechnungsbetrag auf der Jahresrechnung.</li>
              </ul>
            </div>
          </div>

          <div class="basic-card" :class="{ 'expanded': grundpreisExpanded }" @click="toggleGrundpreis">
            <div class="basic-header">
              <h3>
                <i class="fas fa-calendar-alt"></i>
                Grundpreis (Energie)
              </h3>
              <i class="fas fa-chevron-down toggle-icon" :class="{ 'rotated': grundpreisExpanded }"></i>
            </div>
            <div class="basic-content" v-show="grundpreisExpanded">
              <p class="basic-intro">Dieser Bestandteil des Energiepreises ist - im Gegensatz zum Arbeitspreis - vom Verbrauch unabhängig und wird in Euro pro Monat oder auch Euro pro Jahr angegeben. Er macht üblicherweise einen deutlich kleineren Anteil an der Gesamtrechnung aus.</p>
              <div class="tip-box">
                <h4>💡 Tipp für Energiesparer:</h4>
                <p>Inzwischen gibt es Lieferanten, die keinen oder einen sehr geringen Grundpreis verlangen. Solche sogenannten linearen Tarife bieten Anreize zum Energiesparen und sind für Verbraucherinnen/Verbraucher vorteilhaft, weil jede eingesparte Kilowattstunde die Energiekosten direkt mindert.</p>
              </div>
              <div class="tip-box high-consumption">
                <h4>⚡ Tipp für Vielverbraucher:</h4>
                <p>Haben Sie allerdings einen hohen Strombedarf (z.B. wegen einer Wärmepumpe oder anderen verbrauchsintensiven Geräten), ist es für Sie oft günstiger, einen Tarif mit einem ggf. höheren Grundpreis und dafür einen niedrigeren Arbeitspreis zu wählen.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Price Components Overview -->
      <section class="price-overview">
        <h2 class="section-title">
          <i class="fas fa-pie-chart"></i>
          Die drei Hauptkomponenten des Strompreises
        </h2>
        
        <div class="components-grid">
          <div class="component-card">
            <div class="component-icon taxes">
              <i class="fas fa-university"></i>
            </div>
            <div class="component-content">
              <h3>Steuern & Abgaben</h3>
              <div class="percentage">~25%</div>
              <p>Stromsteuer, EEG-Umlage, Netzentgelte und weitere staatlich regulierte Kosten</p>
            </div>
          </div>

          <div class="component-card">
            <div class="component-icon network">
              <i class="fas fa-project-diagram"></i>
            </div>
            <div class="component-content">
              <h3>Netznutzung</h3>
              <div class="percentage">~32%</div>
              <p>Kosten für den Transport des Stroms über die Stromnetze zu Ihnen nach Hause</p>
            </div>
          </div>

          <div class="component-card">
            <div class="component-icon energy">
              <i class="fas fa-bolt"></i>
            </div>
            <div class="component-content">
              <h3>Energiebeschaffung</h3>
              <div class="percentage">~43%</div>
              <p>Kosten für die Stromerzeugung und den Vertrieb - hier können Sie sparen!</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Detailed Breakdown -->
      <section class="detailed-breakdown">
        <h2 class="section-title">
          <i class="fas fa-calculator"></i>
          Detaillierte Aufschlüsselung
        </h2>

        <div class="breakdown-container-centered">
          <div class="breakdown-chart-centered">
            <PriceBreakdownChart />
          </div>
        </div>

      </section>

      <!-- Why Compare Section -->
      <section class="why-compare">
        <h2 class="section-title">
          <i class="fas fa-lightbulb"></i>
          Warum sich ein Vergleich lohnt
        </h2>

        <div class="compare-benefits">
          <div class="benefit-card">
            <div class="benefit-icon">
              <i class="fas fa-percentage"></i>
            </div>
            <h3>Nur 23% sind variabel</h3>
            <p>Während Steuern und Netzentgelte festgelegt sind, können Sie bei der Energiebeschaffung durch einen Anbieterwechsel erheblich sparen.</p>
          </div>

          <div class="benefit-card">
            <div class="benefit-icon">
              <i class="fas fa-euro-sign"></i>
            </div>
            <h3>Bis zu 300€ jährlich sparen</h3>
            <p>Ein durchschnittlicher Haushalt kann durch den Wechsel vom Grundversorger zu einem günstigen Anbieter mehrere hundert Euro pro Jahr sparen.</p>
          </div>

          <div class="benefit-card">
            <div class="benefit-icon">
              <i class="fas fa-leaf"></i>
            </div>
            <h3>Ökostrom oft günstiger</h3>
            <p>Viele Ökostromtarife sind mittlerweile günstiger als der lokale Grundversorgertarif und unterstützen die Energiewende.</p>
          </div>
        </div>
      </section>

      <!-- Market Evolution -->
      <section class="market-evolution">
        <h2 class="section-title">
          <i class="fas fa-chart-line"></i>
          Entwicklung der Strompreise
        </h2>

        <div class="evolution-content">
          <div class="evolution-chart">
            <PriceEvolutionChart />
          </div>

          <div class="evolution-info">
            <h3>Wichtige Trends</h3>
            <ul class="trend-list">
              <li>
                <i class="fas fa-arrow-up text-red"></i>
                <strong>2021-2022:</strong> Starker Anstieg durch Energiekrise
              </li>
              <li>
                <i class="fas fa-balance-scale text-blue"></i>
                <strong>2023:</strong> Stabilisierung auf hohem Niveau
              </li>
              <li>
                <i class="fas fa-arrow-down text-green"></i>
                <strong>2024-2025:</strong> Leichter Rückgang durch Marktberuhigung
              </li>
              <li>
                <i class="fas fa-solar-panel text-green"></i>
                <strong>Zukunft:</strong> Mehr erneuerbare Energien = stabilere Preise
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Tips Section -->
      <section class="tips-section">
        <h2 class="section-title">
          <i class="fas fa-tips"></i>
          Praktische Tipps zum Stromsparen
        </h2>

        <div class="tips-grid">
          <div class="tip-card">
            <div class="tip-icon">
              <i class="fas fa-thermometer-half"></i>
            </div>
            <h4>Heizung optimieren</h4>
            <p>1°C weniger spart 6% Heizkosten. Programmierbare Thermostate helfen beim effizienten Heizen.</p>
          </div>

          <div class="tip-card">
            <div class="tip-icon">
              <i class="fas fa-lightbulb"></i>
            </div>
            <h4>LED-Beleuchtung</h4>
            <p>LED-Lampen verbrauchen 80% weniger Strom als Glühbirnen und halten 25x länger.</p>
          </div>

          <div class="tip-card">
            <div class="tip-icon">
              <i class="fas fa-plug"></i>
            </div>
            <h4>Standby vermeiden</h4>
            <p>Geräte im Standby verbrauchen unnötig Strom. Schaltbare Steckerleisten helfen beim Sparen.</p>
          </div>

          <div class="tip-card">
            <div class="tip-icon">
              <i class="fas fa-washing-machine"></i>
            </div>
            <h4>Effiziente Haushaltsgeräte</h4>
            <p>A+++-Geräte verbrauchen deutlich weniger Strom. Der Mehrpreis amortisiert sich schnell.</p>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="cta-section">
        <div class="cta-card">
          <h2>Jetzt Stromkosten senken!</h2>
          <p>Nutzen Sie unser kostenloses Vergleichstool und finden Sie den besten Tarif für Ihren Bedarf.</p>
          <router-link to="/comparison" class="cta-button">
            <i class="fas fa-calculator"></i>
            Tarife vergleichen
          </router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import PriceEvolutionChart from '../components/PriceEvolutionChart.vue';
import PriceBreakdownChart from '../components/PriceBreakdownChart.vue';

export default {
  name: 'ElectricityPriceInfo',
  components: {
    PriceEvolutionChart,
    PriceBreakdownChart
  },
  data() {
    return {
      arbeitspreisExpanded: false,
      grundpreisExpanded: false
    }
  },
  methods: {
    toggleArbeitspreis() {
      this.arbeitspreisExpanded = !this.arbeitspreisExpanded;
    },
    toggleGrundpreis() {
      this.grundpreisExpanded = !this.grundpreisExpanded;
    }
  },
  mounted() {
    // Scroll to top when component is mounted
    window.scrollTo(0, 0);
  }
}
</script>

<style scoped>
.electricity-price-info {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  color: white;
  padding: 4rem 0;
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.page-title i {
  font-size: 2rem;
}

.page-subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* Section Styling */
section {
  margin: 4rem 0;
}

.section-title {
  font-size: 2rem;
  color: #1f2937;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-title i {
  color: #059669;
}

/* Price Basics */
.basics-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  margin-bottom: 3rem;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.basic-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.basic-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.basic-card.expanded {
  box-shadow: 0 8px 25px rgba(5, 150, 105, 0.15);
  border: 1px solid #10b981;
}

.basic-header {
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f3f4f6;
}

.basic-card.expanded .basic-header {
  border-bottom-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
}

.basic-header h3 {
  font-size: 1.3rem;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.basic-header i.fas {
  color: #059669;
}

.toggle-icon {
  color: #6b7280;
  transition: transform 0.3s ease;
  font-size: 1.2rem;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
  color: #059669;
}

.basic-content {
  padding: 2rem;
  background: #fafafa;
  border-top: 1px solid #e5e7eb;
}

.basic-intro {
  font-size: 1.1rem;
  color: #374151;
  margin-bottom: 1.5rem;
  font-weight: 500;
  line-height: 1.6;
}

.basic-points {
  list-style: none;
  padding: 0;
  margin: 0;
}

.basic-points li {
  position: relative;
  padding-left: 1.5rem;
  margin-bottom: 1rem;
  color: #4b5563;
  line-height: 1.6;
}

.basic-points li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #059669;
  font-weight: bold;
  font-size: 1.2rem;
}

.tip-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1.5rem 0;
}

.tip-box.high-consumption {
  background: #fef3c7;
  border-color: #fbbf24;
}

.tip-box h4 {
  font-size: 1rem;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tip-box p {
  margin: 0;
  color: #374151;
  line-height: 1.6;
}

/* Components Grid */
.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.component-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.component-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.component-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: white;
  flex-shrink: 0;
}

.component-icon.taxes {
  background: linear-gradient(135deg, #dc2626, #ef4444);
}

.component-icon.network {
  background: linear-gradient(135deg, #ea580c, #f97316);
}

.component-icon.energy {
  background: linear-gradient(135deg, #059669, #10b981);
}

.component-content h3 {
  font-size: 1.3rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.percentage {
  font-size: 1.8rem;
  font-weight: 700;
  color: #059669;
  margin-bottom: 1rem;
}

.component-content p {
  color: #6b7280;
  line-height: 1.5;
}

/* Detailed Breakdown */
.breakdown-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.breakdown-container-centered {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  margin: 0;
}

.breakdown-chart-centered {
  width: 100%;
}

.chart-placeholder {
  height: 300px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #64748b;
  text-align: center;
  border: 2px dashed #cbd5e1;
}

.chart-placeholder i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #94a3b8;
}

.detail-category {
  margin-bottom: 2rem;
}

.category-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.taxes-color {
  color: #dc2626;
}

.network-color {
  color: #ea580c;
}

.energy-color {
  color: #059669;
}

.detail-items {
  margin-left: 1.5rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.detail-item:last-child {
  border-bottom: none;
}

.item-name {
  color: #4b5563;
  font-size: 0.9rem;
}

.item-value {
  font-weight: 600;
  color: #1f2937;
}

/* Why Compare Section */
.compare-benefits {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.benefit-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.benefit-card:hover {
  transform: translateY(-4px);
}

.benefit-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #059669, #10b981);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 1.5rem;
  color: white;
}

.benefit-card h3 {
  font-size: 1.2rem;
  color: #1f2937;
  margin-bottom: 1rem;
}

.benefit-card p {
  color: #6b7280;
  line-height: 1.6;
}

/* Market Evolution */
.evolution-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 3rem;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.evolution-chart {
  min-height: 400px;
}

.evolution-info h3 {
  font-size: 1.3rem;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.trend-list {
  list-style: none;
  padding: 0;
}

.trend-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
}

.trend-list i {
  margin-top: 0.25rem;
  width: 16px;
}

.text-red { color: #dc2626; }
.text-blue { color: #059669; }
.text-green { color: #059669; }

/* Tips Section */
.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.tip-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.tip-card:hover {
  transform: translateY(-2px);
}

.tip-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 1.2rem;
  color: white;
}

.tip-card h4 {
  font-size: 1.1rem;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.tip-card p {
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
}

/* CTA Section */
.cta-section {
  text-align: center;
  margin: 4rem 0;
}

.cta-card {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  color: white;
  border-radius: 16px;
  padding: 3rem 2rem;
  max-width: 600px;
  margin: 0 auto;
}

.cta-card h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.cta-card p {
  font-size: 1.1rem;
  opacity: 0.9;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: white;
  color: #059669;
  padding: 1rem 2rem;
  border-radius: 50px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
  transition: all 0.3s ease;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Responsive Design */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
    flex-direction: column;
    gap: 0.5rem;
  }

  .basics-grid {
    grid-template-columns: 1fr;
  }

  .basic-header {
    padding: 1.5rem;
  }

  .basic-content {
    padding: 1.5rem;
  }

  .basic-header h3 {
    font-size: 1.1rem;
  }

  .components-grid {
    grid-template-columns: 1fr;
  }

  .component-card {
    flex-direction: column;
    text-align: center;
  }

  .breakdown-container,
  .evolution-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .compare-benefits {
    grid-template-columns: 1fr;
  }

  .tips-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }

  .cta-card {
    padding: 2rem 1rem;
  }

  .cta-card h2 {
    font-size: 1.5rem;
  }
}
</style>
