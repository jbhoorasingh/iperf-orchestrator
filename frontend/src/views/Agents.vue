<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Agents</h1>
      <button 
        @click="refreshAgents"
        class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading agents...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <div v-else class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="agent in agents" :key="agent.id" class="px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <StatusBadge :status="agent.status" />
              </div>
              <div class="ml-4">
                <div class="text-sm font-medium text-gray-900">{{ agent.name }}</div>
                <div class="text-sm text-gray-500">
                  IP: {{ agent.ip_address || 'Unknown' }} | 
                  OS: {{ agent.operating_system || 'Unknown' }}
                </div>
                <div class="text-sm text-gray-500">
                  Last heartbeat: {{ formatTime(agent.last_heartbeat) }}
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button 
                @click="deleteAgent(agent.id)"
                class="text-red-600 hover:text-red-900 text-sm"
              >
                Delete
              </button>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Create Agent Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Create Agent</h3>
          <form @submit.prevent="createAgent">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
              <input 
                v-model="newAgent.name"
                type="text" 
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="agent1"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Registration Key</label>
              <input 
                v-model="newAgent.registration_key"
                type="text" 
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="your-registration-key"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Operating System</label>
              <input 
                v-model="newAgent.operating_system"
                type="text" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="linux"
              />
            </div>
            <div class="flex justify-end space-x-3">
              <button 
                type="button"
                @click="showCreateModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button 
                type="submit"
                :disabled="loading"
                class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Create Agent Button -->
    <div class="mt-6">
      <button 
        @click="showCreateModal = true"
        class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
      >
        Create Agent
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useApiStore } from '../stores/api'
import StatusBadge from '../components/StatusBadge.vue'

export default {
  name: 'Agents',
  components: {
    StatusBadge
  },
  setup() {
    const apiStore = useApiStore()
    const agents = ref([])
    const loading = ref(false)
    const error = ref('')
    const showCreateModal = ref(false)
    const newAgent = ref({
      name: '',
      registration_key: '',
      operating_system: ''
    })
    let refreshInterval = null

    const fetchAgents = async () => {
      try {
        loading.value = true
        error.value = ''
        agents.value = await apiStore.get('/v1/agents')
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to fetch agents'
      } finally {
        loading.value = false
      }
    }

    const refreshAgents = () => {
      fetchAgents()
    }

    const createAgent = async () => {
      try {
        loading.value = true
        await apiStore.post('/v1/agents', newAgent.value)
        showCreateModal.value = false
        newAgent.value = { name: '', registration_key: '', operating_system: '' }
        await fetchAgents()
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to create agent'
      } finally {
        loading.value = false
      }
    }

    const deleteAgent = async (agentId) => {
      if (confirm('Are you sure you want to delete this agent?')) {
        try {
          await apiStore.del(`/v1/agents/${agentId}`)
          await fetchAgents()
        } catch (err) {
          error.value = err.response?.data?.message || 'Failed to delete agent'
        }
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return 'Never'
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} minutes ago`
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours} hours ago`
      return date.toLocaleString()
    }

    onMounted(() => {
      fetchAgents()
      // Refresh every 5 seconds
      refreshInterval = setInterval(fetchAgents, 5000)
    })

    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      agents,
      loading,
      error,
      showCreateModal,
      newAgent,
      fetchAgents,
      refreshAgents,
      createAgent,
      deleteAgent,
      formatTime
    }
  }
}
</script>
