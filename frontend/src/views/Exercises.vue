<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex justify-between items-center mb-4">
        <h1 class="text-2xl font-bold text-gray-900">Exercises</h1>
        <button
          @click="showCreateModal = true"
          class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center space-x-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Create Exercise</span>
        </button>
      </div>

      <!-- Search and Filters -->
      <div class="bg-white rounded-lg shadow p-4">
        <div class="flex flex-col md:flex-row gap-4">
          <!-- Search Bar -->
          <div class="flex-1">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search exercises by name or notes..."
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          <!-- Status Filter Pills -->
          <div class="flex items-center space-x-2">
            <button
              @click="statusFilter = 'all'"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                statusFilter === 'all'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              All
            </button>
            <button
              @click="statusFilter = 'not_started'"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                statusFilter === 'not_started'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Not Started
            </button>
            <button
              @click="statusFilter = 'in_progress'"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                statusFilter === 'in_progress'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              In Progress
            </button>
            <button
              @click="statusFilter = 'completed'"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                statusFilter === 'completed'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Completed
            </button>
          </div>
        </div>

        <!-- Results Count -->
        <div class="mt-3 text-sm text-gray-600">
          Showing {{ filteredExercises.length }} of {{ exercises.length }} exercises
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading exercises...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Exercise Cards -->
    <div v-else-if="filteredExercises.length === 0" class="bg-white rounded-lg shadow p-8 text-center">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No exercises found</h3>
      <p class="mt-1 text-sm text-gray-500">
        {{ searchQuery || statusFilter !== 'all' ? 'Try adjusting your filters' : 'Get started by creating a new exercise' }}
      </p>
    </div>

    <div v-else class="grid gap-4">
      <div
        v-for="exercise in filteredExercises"
        :key="exercise.id"
        class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
      >
        <div class="p-5">
          <div class="flex items-start justify-between">
            <!-- Left Side: Main Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center space-x-3 mb-2">
                <h3 class="text-lg font-semibold text-gray-900 truncate">{{ exercise.name }}</h3>
                <!-- Status Badge -->
                <span
                  :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    getStatusColor(exercise)
                  ]"
                >
                  {{ getStatusText(exercise) }}
                </span>
              </div>

              <!-- Notes -->
              <p v-if="exercise.notes" class="text-sm text-gray-600 mb-3 line-clamp-2">
                {{ exercise.notes }}
              </p>

              <!-- Metadata Grid -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div class="flex items-center text-gray-500">
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{{ exercise.duration_seconds }}s</span>
                </div>

                <div class="flex items-center text-gray-500">
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <span>ID: {{ exercise.id }}</span>
                </div>

                <div v-if="exercise.started_at" class="flex items-center text-gray-500">
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Started: {{ formatShortTime(exercise.started_at) }}</span>
                </div>

                <div v-if="exercise.ended_at" class="flex items-center text-gray-500">
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Ended: {{ formatShortTime(exercise.ended_at) }}</span>
                </div>

                <div class="flex items-center text-gray-500">
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Created: {{ formatShortTime(exercise.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- Right Side: Action Button -->
            <div class="ml-4 flex-shrink-0">
              <router-link
                :to="`/exercises/${exercise.id}`"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                View Details
                <svg class="ml-2 -mr-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Exercise Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Create Exercise</h3>
          <form @submit.prevent="createExercise">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
              <input 
                v-model="newExercise.name"
                type="text" 
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Exercise 1"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Duration (seconds)</label>
              <input 
                v-model.number="newExercise.duration_seconds"
                type="number" 
                required
                min="1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="30"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Notes</label>
              <textarea 
                v-model="newExercise.notes"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Optional notes..."
              ></textarea>
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
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useApiStore } from '../stores/api'

export default {
  name: 'Exercises',
  setup() {
    const apiStore = useApiStore()
    const exercises = ref([])
    const loading = ref(false)
    const error = ref('')
    const showCreateModal = ref(false)
    const searchQuery = ref('')
    const statusFilter = ref('all')
    const newExercise = ref({
      name: '',
      duration_seconds: 30,
      notes: ''
    })

    const getErrorMessage = (err) => {
      if (!err.response) return 'Network error - please check your connection'
      const data = err.response.data
      if (data?.detail?.message) return data.detail.message
      if (typeof data?.detail === 'string') return data.detail
      if (data?.message) return data.message
      return `Error: ${err.response.status}`
    }

    const fetchExercises = async () => {
      try {
        loading.value = true
        error.value = ''
        exercises.value = await apiStore.get('/v1/exercises')
      } catch (err) {
        error.value = getErrorMessage(err)
      } finally {
        loading.value = false
      }
    }

    const createExercise = async () => {
      try {
        loading.value = true
        error.value = ''
        await apiStore.post('/v1/exercises', newExercise.value)
        showCreateModal.value = false
        newExercise.value = { name: '', duration_seconds: 30, notes: '' }
        await fetchExercises()
      } catch (err) {
        error.value = getErrorMessage(err)
      } finally {
        loading.value = false
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return 'Never'
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    const formatShortTime = (timestamp) => {
      if (!timestamp) return 'Never'
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`

      // Format as MM/DD/YY HH:mm
      return date.toLocaleString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const getStatusText = (exercise) => {
      if (exercise.ended_at) return 'Completed'
      if (exercise.started_at) return 'In Progress'
      return 'Not Started'
    }

    const getStatusColor = (exercise) => {
      if (exercise.ended_at) return 'bg-green-100 text-green-800'
      if (exercise.started_at) return 'bg-blue-100 text-blue-800'
      return 'bg-gray-100 text-gray-800'
    }

    const getExerciseStatus = (exercise) => {
      if (exercise.ended_at) return 'completed'
      if (exercise.started_at) return 'in_progress'
      return 'not_started'
    }

    // Computed filtered exercises
    const filteredExercises = computed(() => {
      let filtered = exercises.value

      // Apply status filter
      if (statusFilter.value !== 'all') {
        filtered = filtered.filter(ex => getExerciseStatus(ex) === statusFilter.value)
      }

      // Apply search filter
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(ex => {
          return ex.name.toLowerCase().includes(query) ||
                 (ex.notes && ex.notes.toLowerCase().includes(query))
        })
      }

      return filtered
    })

    onMounted(() => {
      fetchExercises()
    })

    return {
      exercises,
      loading,
      error,
      showCreateModal,
      searchQuery,
      statusFilter,
      newExercise,
      fetchExercises,
      createExercise,
      formatTime,
      formatShortTime,
      getStatusText,
      getStatusColor,
      filteredExercises
    }
  }
}
</script>
