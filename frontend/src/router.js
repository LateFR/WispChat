import { createRouter, createWebHistory } from 'vue-router'
import MainApp from './components/MainApp.vue'
import Login from './components/Login.vue'
import LoadingMatch from './components/Loading.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/', component: MainApp },
  { path: '/loading', component: LoadingMatch },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router