<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Exercises</h1>
      <button 
        @click="showCreateModal = true"
        class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
      >
        Create Exercise
      </button>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading exercises...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <div v-else class="grid gap-6">
      <div v-for="exercise in exercises" :key="exercise.id" class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-medium text-gray-900">{{ exercise.name }}</h3>
            <p class="text-sm text-gray-500">
              Duration: {{ exercise.duration_seconds }}s | 
              Created: {{ formatTime(exercise.created_at) }}
            </p>
            <p v-if="exercise.notes" class="text-sm text-gray-600 mt-1">{{ exercise.notes }}</p>
          </div>
          <div class="flex items-center space-x-2">
            <router-link
              :to="`/exercises/${exercise.id}`"
              class="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
            >
              View Details
            </router-link>
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
import { ref, onMounted } from 'vue'
import { useApiStore } from '../stores/api'

export default {
  name: 'Exercises',
  setup() {
    const apiStore = useApiStore()
    const exercises = ref([])
    const loading = ref(false)
    const error = ref('')
    const showCreateModal = ref(false)
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

    onMounted(() => {
      fetchExercises()
    })

    return {
      exercises,
      loading,
      error,
      showCreateModal,
      newExercise,
      fetchExercises,
      createExercise,
      formatTime
    }
  }
}
</script>
