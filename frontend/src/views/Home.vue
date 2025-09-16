<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1>Stromtarife einfach vergleichen</h1>
          <p>Finden Sie den günstigsten Tarif für Ihren Verbrauch und sparen Sie Geld</p>
          
          <div class="hero-actions">
            <router-link to="/comparison" class="btn btn-primary btn-large">
              <i class="fas fa-calculator"></i>
              Jetzt vergleichen
            </router-link>
          </div>
          
          <div class="hero-stats">
            <div class="stat">
              <div class="stat-number">2 Min</div>
              <div class="stat-label">Zeit für Vergleich</div>
            </div>
            <div class="stat">
              <div class="stat-number">100%</div>
              <div class="stat-label">Kostenlos</div>
            </div>
            <div class="stat">
              <div class="stat-number">Einfach</div>
              <div class="stat-label">Zu bedienen</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-it-works py-16">
      <div class="container">
        <h2 class="text-center text-3xl font-bold mb-8">So einfach geht's</h2>
        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3>Daten eingeben</h3>
              <p>Geben Sie Details, wie Ihren Jahresverbrauch, ein oder laden Sie Diesen in einer CSV-Datei hoch.</p>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3>Tarife vergleichen</h3>
              <p>Sehen Sie alle verfügbaren Tarife übersichtlich sortiert</p>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3>Besten Tarif wählen</h3>
              <p>Entscheiden Sie sich für den Tarif, der am besten zu Ihnen passt</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'Home'
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
  
  .steps {
    grid-template-columns: 1fr;
  }
}
</style>
