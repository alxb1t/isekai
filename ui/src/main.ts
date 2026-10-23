import * as pinia from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './styles.css'
import './app.css'

createApp(App).use(pinia.createPinia()).use(router).mount('#app')
