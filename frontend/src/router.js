import { createRouter, createWebHistory } from 'vue-router'
import App from './components/Chat.vue'
import Login from './components/Login.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/', component: App }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router