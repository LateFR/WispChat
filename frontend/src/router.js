import { createRouter, createWebHistory } from 'vue-router'
import App from './components/Chat.vue'
import Login from './components/Login.vue'
import LoadingMatch from './components/LoadingMatch.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/', component: App },
  { path: '/loading', component: LoadingMatch }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router