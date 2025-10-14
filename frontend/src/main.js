import './main.css'

const cssLink = document.createElement('link');
cssLink.rel = 'stylesheet';
cssLink.href = import.meta.env.MODE === 'production'
  ? '/css/daisy-min.css'   // fichier minifié dans /public/css/
  : '/css/daisy-full.css'; // fichier complet pour dev
document.head.appendChild(cssLink);

import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'
import { createPinia } from 'pinia'

const app = createApp(App)
app.use(router)
const pinia = createPinia()
app.use(pinia)
app.mount('#app')