import { createRouter, createWebHistory } from 'vue-router'

import Overview from '../views/Overview.vue'
import Incidents from '../views/Incidents.vue'
import Errors from '../views/Errors.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Overview },
  { path: '/incidents', component: Incidents },
  { path: '/errors', component: Errors }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router