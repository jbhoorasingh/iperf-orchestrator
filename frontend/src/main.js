import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'
import router from './router'

// Import stores
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

// Initialize Pinia first
app.use(pinia)
app.use(router)

// Navigation guard (after Pinia is initialized)
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.name !== 'Login' && !authStore.isAuthenticated) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Agents' })
  } else {
    next()
  }
})

app.mount('#app')
