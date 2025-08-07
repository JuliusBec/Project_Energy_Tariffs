<template>
  <header class="header">
    <div class="container">
      <div class="header-content">
        <router-link to="/" class="logo">
          <i class="fas fa-bolt"></i>
          <span>EnergyCompare</span>
        </router-link>
        
        <nav class="nav">
          <router-link to="/" class="nav-link">
            <i class="fas fa-home"></i>
            <span>Home</span>
          </router-link>
          <router-link to="/comparison" class="nav-link">
            <i class="fas fa-calculator"></i>
            <span>Tarifrechner</span>
          </router-link>
          <router-link to="/market" class="nav-link">
            <i class="fas fa-chart-line"></i>
            <span>Marktdaten</span>
          </router-link>
          <router-link to="/tips" class="nav-link">
            <i class="fas fa-lightbulb"></i>
            <span>Spartipps</span>
          </router-link>
        </nav>
        
        <button @click="toggleMobileMenu" class="mobile-menu-btn">
          <i class="fas fa-bars"></i>
        </button>
      </div>
      
      <!-- Mobile Menu -->
      <div v-if="showMobileMenu" class="mobile-menu">
        <router-link to="/" class="mobile-nav-link" @click="closeMobileMenu">
          <i class="fas fa-home"></i>
          <span>Home</span>
        </router-link>
        <router-link to="/comparison" class="mobile-nav-link" @click="closeMobileMenu">
          <i class="fas fa-calculator"></i>
          <span>Tarifrechner</span>
        </router-link>
        <router-link to="/market" class="mobile-nav-link" @click="closeMobileMenu">
          <i class="fas fa-chart-line"></i>
          <span>Marktdaten</span>
        </router-link>
        <router-link to="/tips" class="mobile-nav-link" @click="closeMobileMenu">
          <i class="fas fa-lightbulb"></i>
          <span>Spartipps</span>
        </router-link>
      </div>
    </div>
  </header>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Header',
  setup() {
    const showMobileMenu = ref(false)
    
    const toggleMobileMenu = () => {
      showMobileMenu.value = !showMobileMenu.value
    }
    
    const closeMobileMenu = () => {
      showMobileMenu.value = false
    }
    
    return {
      showMobileMenu,
      toggleMobileMenu,
      closeMobileMenu
    }
  }
}
</script>

<style scoped>
.header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #059669;
  text-decoration: none;
  transition: color 0.2s;
}

.logo:hover {
  color: #047857;
}

.logo i {
  font-size: 1.75rem;
}

.nav {
  display: flex;
  gap: 2rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: #6b7280;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: #059669;
  background-color: #f8fafc;
}

.nav-link.router-link-active {
  color: #059669;
  background-color: #f0fdf4;
}

.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.5rem;
}

.mobile-menu {
  display: none;
  border-top: 1px solid #e5e7eb;
  padding: 1rem 0;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: #6b7280;
  font-weight: 500;
  padding: 0.75rem 0;
  transition: color 0.2s;
}

.mobile-nav-link:hover {
  color: #059669;
}

.mobile-nav-link.router-link-active {
  color: #059669;
}

@media (max-width: 768px) {
  .nav {
    display: none;
  }
  
  .mobile-menu-btn {
    display: block;
  }
  
  .mobile-menu {
    display: block;
  }
}
</style>
