import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// Import views
import Login from './views/Login.vue'
import Agents from './views/Agents.vue'
import Exercises from './views/Exercises.vue'
import ExerciseDetail from './views/ExerciseDetail.vue'
import Tasks from './views/Tasks.vue'

// Import stores
import { useAuthStore } from './stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/', redirect: '/agents' },
  { path: '/agents', name: 'Agents', component: Agents },
  { path: '/exercises', name: 'Exercises', component: Exercises },
  { path: '/exercises/:id', name: 'ExerciseDetail', component: ExerciseDetail },
  { path: '/tasks', name: 'Tasks', component: Tasks }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

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
