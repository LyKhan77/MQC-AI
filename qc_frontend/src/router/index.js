import { createRouter, createWebHistory } from 'vue-router'
import LiveMonitor from '../views/LiveMonitor.vue'
import QCStudio from '../views/QCStudio.vue'
import BatchHistory from '../views/BatchHistory.vue'
import Reports from '../views/Reports.vue'
import AuditLog from '../views/AuditLog.vue'
import Settings from '../views/Settings.vue'
import MediaDetection from '../views/MediaDetection.vue'
import QuantityDetection from '../views/QuantityDetection.vue'
import QuantityHistory from '../views/QuantityHistory.vue'

const routes = [
  { path: '/', redirect: '/live' },
  { path: '/live', name: 'live', component: LiveMonitor },
  { path: '/qc', name: 'qc', component: QCStudio },
  { path: '/batches', name: 'batches', component: BatchHistory },
  { path: '/media-detection', name: 'media', component: MediaDetection },
  { path: '/quantity', name: 'quantity', component: QuantityDetection },
  { path: '/quantity/history', name: 'quantity-history', component: QuantityHistory },
  { path: '/reports', name: 'reports', component: Reports },
  { path: '/audit', name: 'audit', component: AuditLog },
  { path: '/settings', name: 'settings', component: Settings },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
