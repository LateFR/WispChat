import './main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'
import { createPinia } from 'pinia'
import ws from '@/services/ws'

const app = createApp(App)
app.use(router)
const pinia = createPinia()
app.use(pinia)
app.mount('#app')
ws.initWebSocket()