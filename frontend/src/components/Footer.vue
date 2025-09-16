<template>
  <footer class="footer">
    <div class="container">
      <div class="footer-content">
        <div class="footer-section">
          <div class="logo">
            <i class="fas fa-bolt"></i>
            <span>Stromtarif Vergleich</span>
          </div>
          <p>Einfach, schnell und kostenlos Stromtarife vergleichen</p>
        </div>
        
        <div class="footer-section">
          <h4>Navigation</h4>
          <ul>
            <li><router-link to="/">Startseite</router-link></li>
            <li><router-link to="/comparison">Tarifrechner</router-link></li>
            <li><router-link to="/tips">Spartipps</router-link></li>
          </ul>
        </div>
      </div>
      
      <div class="footer-bottom">
        <p>&copy; 2025 Stromtarif Vergleich Tool</p>
        <p class="version">Version 1.0.0</p>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'Footer'
}
</script>

<style scoped>
.footer {
  background: #1f2937;
  color: #d1d5db;
  padding: 3rem 0 1rem;
  margin-top: auto;
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.footer-section:last-child {
  text-align: right;
}

.footer-section .logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #059669;
  margin-bottom: 1rem;
}

.footer-section .logo i {
  font-size: 1.75rem;
}

.footer-section p {
  margin-bottom: 1rem;
  color: #9ca3af;
}

.footer-section h4 {
  color: #ffffff;
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 1.1rem;
}

.footer-section ul {
  list-style: none;
}

.footer-section ul li {
  margin-bottom: 0.5rem;
}

.footer-section ul li a {
  color: #d1d5db;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-section ul li a:hover {
  color: #ffffff;
}

.social-links {
  display: flex;
  gap: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #374151;
  border-radius: 8px;
  color: #d1d5db;
  text-decoration: none;
  transition: all 0.2s;
}

.social-link:hover {
  background: #059669;
  color: #ffffff;
  transform: translateY(-2px);
}

.footer-bottom {
  border-top: 1px solid #374151;
  padding-top: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #9ca3af;
  font-size: 0.9rem;
}

.version {
  font-size: 0.8rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .footer-bottom {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>
