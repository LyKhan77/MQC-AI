import { createRouter, createWebHistory } from 'vue-router'
import LiveMonitor from '../views/LiveMonitor.vue'
import QCStudio from '../views/QCStudio.vue'

const routes = [
  { path: '/', redirect: '/live' },
  { path: '/live', component: LiveMonitor },
  { path: '/qc', component: QCStudio },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
