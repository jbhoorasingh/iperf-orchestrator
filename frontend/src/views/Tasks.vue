<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Tasks</h1>
      <button 
        @click="refreshTasks"
        class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
      >
        Refresh
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Agent</label>
          <select 
            v-model="filters.agent_id"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Agents</option>
            <option v-for="agent in agents" :key="agent.id" :value="agent.id">
              {{ agent.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select 
            v-model="filters.status"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="accepted">Accepted</option>
            <option value="running">Running</option>
            <option value="succeeded">Succeeded</option>
            <option value="failed">Failed</option>
            <option value="canceled">Canceled</option>
            <option value="timed_out">Timed Out</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
          <select 
            v-model="filters.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Types</option>
            <option value="iperf_server_start">Server Start</option>
            <option value="iperf_client_run">Client Run</option>
            <option value="kill_all">Kill All</option>
            <option value="iperf_server_stop">Server Stop</option>
          </select>
        </div>
        <div class="flex items-end">
          <button 
            @click="applyFilters"
            class="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading tasks...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <div v-else class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="task in tasks" :key="task.id" class="px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <StatusBadge :status="task.status" />
              </div>
              <div class="ml-4">
                <div class="text-sm font-medium text-gray-900">
                  Task #{{ task.id }} - {{ task.type }}
                </div>
                <div class="text-sm text-gray-500">
                  Agent: {{ getAgentName(task.agent_id) }}
                </div>
                <div class="text-sm text-gray-500">
                  Created: {{ formatTime(task.created_at) }}
                  <span v-if="task.started_at"> | Started: {{ formatTime(task.started_at) }}</span>
                  <span v-if="task.finished_at"> | Finished: {{ formatTime(task.finished_at) }}</span>
                </div>
                <div v-if="task.error" class="text-sm text-red-600 mt-1">
                  Error: {{ task.error }}
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button 
                @click="viewTaskDetails(task)"
                class="text-indigo-600 hover:text-indigo-900 text-sm"
              >
                View Details
              </button>
              <button 
                v-if="task.status === 'running' || task.status === 'accepted'"
                @click="cancelTask(task.id)"
                class="text-red-600 hover:text-red-900 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Task Details Modal -->
    <div v-if="selectedTask" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-3/4 max-w-4xl shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              Task #{{ selectedTask.id }} - {{ selectedTask.type }}
            </h3>
            <button 
              @click="selectedTask = null"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 class="font-medium text-gray-900 mb-2">Task Information</h4>
              <div class="space-y-2 text-sm">
                <div><span class="font-medium">Status:</span> <StatusBadge :status="selectedTask.status" /></div>
                <div><span class="font-medium">Agent:</span> {{ getAgentName(selectedTask.agent_id) }}</div>
                <div><span class="font-medium">Created:</span> {{ formatTime(selectedTask.created_at) }}</div>
                <div v-if="selectedTask.accepted_at"><span class="font-medium">Accepted:</span> {{ formatTime(selectedTask.accepted_at) }}</div>
                <div v-if="selectedTask.started_at"><span class="font-medium">Started:</span> {{ formatTime(selectedTask.started_at) }}</div>
                <div v-if="selectedTask.finished_at"><span class="font-medium">Finished:</span> {{ formatTime(selectedTask.finished_at) }}</div>
              </div>
            </div>
            
            <div>
              <h4 class="font-medium text-gray-900 mb-2">Payload</h4>
              <pre class="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-40">{{ JSON.stringify(selectedTask.payload, null, 2) }}</pre>
            </div>
          </div>
          
          <div v-if="selectedTask.result" class="mt-4">
            <h4 class="font-medium text-gray-900 mb-2">Result</h4>
            <pre class="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-40">{{ JSON.stringify(selectedTask.result, null, 2) }}</pre>
          </div>
          
          <div v-if="selectedTask.error" class="mt-4">
            <h4 class="font-medium text-gray-900 mb-2">Error</h4>
            <pre class="bg-red-50 p-3 rounded text-xs text-red-600">{{ selectedTask.error }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useApiStore } from '../stores/api'
import StatusBadge from '../components/StatusBadge.vue'

export default {
  name: 'Tasks',
  components: {
    StatusBadge
  },
  setup() {
    const apiStore = useApiStore()
    const tasks = ref([])
    const agents = ref([])
    const loading = ref(false)
    const error = ref('')
    const selectedTask = ref(null)
    const filters = ref({
      agent_id: '',
      status: '',
      type: ''
    })

    const fetchTasks = async () => {
      try {
        loading.value = true
        error.value = ''
        
        const params = new URLSearchParams()
        if (filters.value.agent_id) params.append('agent_id', filters.value.agent_id)
        if (filters.value.status) params.append('status', filters.value.status)
        if (filters.value.type) params.append('type', filters.value.type)
        
        const queryString = params.toString()
        const url = queryString ? `/v1/tasks?${queryString}` : '/v1/tasks'
        
        tasks.value = await apiStore.get(url)
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to fetch tasks'
      } finally {
        loading.value = false
      }
    }

    const fetchAgents = async () => {
      try {
        agents.value = await apiStore.get('/v1/agents')
      } catch (err) {
        console.error('Failed to fetch agents:', err)
      }
    }

    const applyFilters = () => {
      fetchTasks()
    }

    const refreshTasks = () => {
      fetchTasks()
    }

    const viewTaskDetails = (task) => {
      selectedTask.value = task
    }

    const cancelTask = async (taskId) => {
      if (confirm('Are you sure you want to cancel this task?')) {
        try {
          await apiStore.post(`/v1/tasks/${taskId}/cancel`)
          await fetchTasks()
        } catch (err) {
          error.value = err.response?.data?.message || 'Failed to cancel task'
        }
      }
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
      fetchTasks()
      fetchAgents()
    })

    return {
      tasks,
      agents,
      loading,
      error,
      selectedTask,
      filters,
      fetchTasks,
      applyFilters,
      refreshTasks,
      viewTaskDetails,
      cancelTask,
      getAgentName,
      formatTime
    }
  }
}
</script>
