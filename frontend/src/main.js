import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './views/Home.vue'
import TariffComparison from './views/TariffComparison.vue'
import SavingsTips from './views/SavingsTips.vue'
import ElectricityPriceInfo from './views/ElectricityPriceInfo.vue'

// CSS Import
import './style.css'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/comparison', name: 'TariffComparison', component: TariffComparison },
  { path: '/tips', name: 'SavingsTips', component: SavingsTips },
  { path: '/price-info', name: 'ElectricityPriceInfo', component: ElectricityPriceInfo }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

createApp(App).use(router).mount('#app')
