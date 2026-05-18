import { createRouter, createWebHistory } from 'vue-router'
import Detection from '../views/Detection.vue'

const routes = [
  {
    path: '/',
    name: 'Detection',
    component: Detection
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router