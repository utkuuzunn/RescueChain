import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router' // Router'ı import et

createApp(App)
  .use(router) // Router'ı kullan
  .mount('#app')
