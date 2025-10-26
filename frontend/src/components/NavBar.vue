<template>
  <nav class="bg-white shadow-sm border-b">
    <div class="container mx-auto px-4">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center space-x-8">
          <h1 class="text-xl font-bold text-gray-900">Iperf Orchestrator</h1>
          <div class="flex space-x-4">
            <router-link 
              to="/agents" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.name === 'Agents' }"
            >
              Agents
            </router-link>
            <router-link 
              to="/exercises" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.name === 'Exercises' }"
            >
              Exercises
            </router-link>
            <router-link 
              to="/tasks" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.name === 'Tasks' }"
            >
              Tasks
            </router-link>
          </div>
        </div>
        <div class="flex items-center">
          <button 
            @click="logout"
            class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

export default {
  name: 'NavBar',
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()

    const logout = () => {
      authStore.logout()
      router.push({ name: 'Login' })
    }

    return {
      logout
    }
  }
}
</script>
