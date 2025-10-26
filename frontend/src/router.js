import { createRouter, createWebHistory } from 'vue-router'

// Import views
import Login from './views/Login.vue'
import Agents from './views/Agents.vue'
import Exercises from './views/Exercises.vue'
import ExerciseDetail from './views/ExerciseDetail.vue'
import Tasks from './views/Tasks.vue'

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

export default router
