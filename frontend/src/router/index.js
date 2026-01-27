import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import Monitor from '../views/Monitor.vue'
import Traceability from '../views/Traceability.vue'
import Counting from '../views/Counting.vue'
import QCStation from '../views/QCStation.vue'
import Settings from '../views/Settings.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard },
      { path: 'monitor', component: Monitor },
      { path: 'traceability', component: Traceability },
      { path: 'counting', component: Counting },
      { path: 'qc-station', component: QCStation },
      { path: 'settings', component: Settings },
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if (to.path === '/login' && isAuthenticated) {
    next('/dashboard');
  } else {
    next();
  }
});

export default router
