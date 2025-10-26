<template>
  <div>
    <div class="mb-6">
      <router-link to="/exercises" class="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
        ← Back to Exercises
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading exercise...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <div v-else-if="exercise">
      <!-- Exercise Header -->
      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ exercise.name }}</h1>
            <p class="text-gray-600">
              Duration: {{ exercise.duration_seconds }}s | 
              Created: {{ formatTime(exercise.created_at) }}
            </p>
            <p v-if="exercise.notes" class="text-gray-600 mt-1">{{ exercise.notes }}</p>
          </div>
          <div class="flex space-x-3">
            <button 
              @click="startExercise"
              :disabled="exercise.started_at"
              class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {{ exercise.started_at ? 'Started' : 'Start Exercise' }}
            </button>
            <button 
              @click="stopExercise"
              :disabled="!exercise.started_at || exercise.ended_at"
              class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
            >
              {{ exercise.ended_at ? 'Stopped' : 'Stop Exercise' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tests Section -->
      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-medium text-gray-900">Tests</h2>
          <button 
            @click="showAddTestModal = true"
            class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            Add Test
          </button>
        </div>

        <div v-if="tests.length === 0" class="text-center py-8 text-gray-500">
          No tests added yet. Click "Add Test" to get started.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Server</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Port</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UDP</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Parallel</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="test in tests" :key="test.id">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ getAgentName(test.server_agent_id) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ getAgentName(test.client_agent_id) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ test.server_port }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ test.udp ? 'Yes' : 'No' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ test.parallel }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ test.time_seconds || exercise.duration_seconds }}s
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <StatusBadge :status="getTestStatus(test)" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Port Reservations -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Port Reservations</h2>
        <div v-if="reservations.length === 0" class="text-center py-4 text-gray-500">
          No active port reservations
        </div>
        <div v-else class="grid gap-2">
          <div v-for="reservation in reservations" :key="reservation.id" 
               class="flex items-center justify-between p-3 bg-gray-50 rounded-md">
            <span class="text-sm text-gray-900">
              Agent {{ reservation.agent_id }}:{{ reservation.port }}
            </span>
            <span class="text-xs text-gray-500">
              {{ formatTime(reservation.created_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Test Modal -->
    <div v-if="showAddTestModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Add Test</h3>
          <form @submit.prevent="addTest">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Server Agent</label>
              <select 
                v-model="newTest.server_agent_id"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select Agent</option>
                <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                  {{ agent.name }} ({{ agent.ip_address }})
                </option>
              </select>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Client Agent</label>
              <select 
                v-model="newTest.client_agent_id"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select Agent</option>
                <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                  {{ agent.name }} ({{ agent.ip_address }})
                </option>
              </select>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Server Port</label>
              <input 
                v-model.number="newTest.server_port"
                type="number" 
                required
                min="1024"
                max="65535"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="5200"
              />
            </div>
            <div class="mb-4">
              <label class="flex items-center">
                <input 
                  v-model="newTest.udp"
                  type="checkbox" 
                  class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span class="ml-2 text-sm text-gray-700">UDP</span>
              </label>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Parallel Streams</label>
              <input 
                v-model.number="newTest.parallel"
                type="number" 
                required
                min="1"
                max="32"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="1"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Time (seconds)</label>
              <input 
                v-model.number="newTest.time_seconds"
                type="number" 
                min="1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                :placeholder="exercise.duration_seconds"
              />
            </div>
            <div class="flex justify-end space-x-3">
              <button 
                type="button"
                @click="showAddTestModal = false"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button 
                type="submit"
                :disabled="loading"
                class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                Add Test
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useApiStore } from '../stores/api'
import StatusBadge from '../components/StatusBadge.vue'

export default {
  name: 'ExerciseDetail',
  components: {
    StatusBadge
  },
  setup() {
    const route = useRoute()
    const apiStore = useApiStore()
    const exercise = ref(null)
    const tests = ref([])
    const tasks = ref([])
    const agents = ref([])
    const reservations = ref([])
    const loading = ref(false)
    const error = ref('')
    const showAddTestModal = ref(false)
    const newTest = ref({
      server_agent_id: '',
      client_agent_id: '',
      server_port: 5200,
      udp: false,
      parallel: 1,
      time_seconds: null
    })

    const getErrorMessage = (err) => {
      if (!err.response) return 'Network error - please check your connection'
      const data = err.response.data
      if (data?.detail?.message) return data.detail.message
      if (typeof data?.detail === 'string') return data.detail
      if (data?.message) return data.message
      return `Error: ${err.response.status}`
    }

    const fetchExercise = async () => {
      try {
        loading.value = true
        error.value = ''
        const data = await apiStore.get(`/v1/exercises/${route.params.id}`)
        // Backend returns a flat structure with tests and tasks included
        tests.value = data.tests || []
        tasks.value = data.tasks || []
        // Extract exercise fields (everything except tests and tasks)
        const { tests: _, tasks: __, ...exerciseData } = data
        exercise.value = exerciseData
      } catch (err) {
        error.value = getErrorMessage(err)
      } finally {
        loading.value = false
      }
    }

    const fetchAgents = async () => {
      try {
        agents.value = await apiStore.get('/v1/agents')
      } catch (err) {
        error.value = getErrorMessage(err)
      }
    }

    const fetchReservations = async () => {
      try {
        reservations.value = await apiStore.get('/v1/ports/reservations')
      } catch (err) {
        console.error('Failed to fetch reservations:', err)
      }
    }

    const addTest = async () => {
      try {
        loading.value = true
        error.value = ''
        await apiStore.post(`/v1/exercises/${route.params.id}/tests`, newTest.value)
        showAddTestModal.value = false
        newTest.value = {
          server_agent_id: '',
          client_agent_id: '',
          server_port: 5200,
          udp: false,
          parallel: 1,
          time_seconds: null
        }
        await fetchExercise()
        await fetchReservations()
      } catch (err) {
        error.value = getErrorMessage(err)
      } finally {
        loading.value = false
      }
    }

    const startExercise = async () => {
      try {
        error.value = ''
        await apiStore.post(`/v1/exercises/${route.params.id}/start`)
        await fetchExercise()
      } catch (err) {
        error.value = getErrorMessage(err)
      }
    }

    const stopExercise = async () => {
      try {
        error.value = ''
        await apiStore.post(`/v1/exercises/${route.params.id}/stop`)
        await fetchExercise()
        await fetchReservations()
      } catch (err) {
        error.value = getErrorMessage(err)
      }
    }

    const getTestStatus = (test) => {
      // Find corresponding tasks and determine status
      const serverTask = test.server_task_id ? tasks.value.find(t => t.id === test.server_task_id) : null
      const clientTask = test.client_task_id ? tasks.value.find(t => t.id === test.client_task_id) : null

      if (clientTask && clientTask.status) return clientTask.status
      if (serverTask && serverTask.status) return serverTask.status
      return 'pending'
    }

    const getAgentName = (agentId) => {
      const agent = agents.value.find(a => a.id === agentId)
      return agent ? agent.name : `Agent ${agentId}`
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return 'Never'
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    onMounted(() => {
      fetchExercise()
      fetchAgents()
      fetchReservations()
    })

    return {
      exercise,
      tests,
      tasks,
      agents,
      reservations,
      loading,
      error,
      showAddTestModal,
      newTest,
      addTest,
      startExercise,
      stopExercise,
      getTestStatus,
      getAgentName,
      formatTime
    }
  }
}
</script>
