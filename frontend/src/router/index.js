import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import AdminPanel from '../views/AdminPanel.vue'
import StaffPanel from '../views/StaffPanel.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Login },
    { path: '/admin', component: AdminPanel },
    { path: '/staff/:id', component: StaffPanel } // Örn: /staff/1 (İstanbul)
  ]
})

export default router
