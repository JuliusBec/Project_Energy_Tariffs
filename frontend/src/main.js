import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './views/Home.vue'
import TariffComparison from './views/TariffComparison.vue'
import MarketData from './views/MarketData.vue'
import SavingsTips from './views/SavingsTips.vue'

// CSS Import
import './style.css'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/comparison', name: 'TariffComparison', component: TariffComparison },
  { path: '/market', name: 'MarketData', component: MarketData },
  { path: '/tips', name: 'SavingsTips', component: SavingsTips }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

createApp(App).use(router).mount('#app')
