<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <NavBar v-if="isAuthenticated" />
    <main class="container mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useAuthStore } from './stores/auth'
import NavBar from './components/NavBar.vue'

export default {
  name: 'App',
  components: {
    NavBar
  },
  setup() {
    const authStore = useAuthStore()
    
    return {
      isAuthenticated: computed(() => authStore.isAuthenticated)
    }
  }
}
</script>
