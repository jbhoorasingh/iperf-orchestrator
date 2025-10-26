<template>
  <div>
    <div class="mb-6">
      <router-link to="/exercises" class="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
        ← Back to Exercises
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading results...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <div v-else-if="results">
      <h1 class="text-2xl font-bold text-gray-900 mb-6">Exercise Results</h1>

      <!-- Aggregate Metrics -->
      <div v-if="results.aggregate && Object.keys(results.aggregate).length > 0" 
           class="bg-white shadow rounded-lg p-6 mb-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Aggregate Metrics</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div v-if="results.aggregate.bps_avg" class="text-center">
            <div class="text-2xl font-bold text-indigo-600">
              {{ formatBps(results.aggregate.bps_avg) }}
            </div>
            <div class="text-sm text-gray-500">Average Throughput</div>
          </div>
        </div>
      </div>

      <!-- Test Results -->
      <div class="grid gap-6">
        <div v-for="test in results.tests" :key="test.test_id" 
             class="bg-white shadow rounded-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              Test #{{ test.test_id }}
            </h3>
            <StatusBadge :status="test.status" />
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <div class="text-sm text-gray-500">Server</div>
              <div class="font-medium">Agent {{ test.server.agent_id }}:{{ test.server.port }}</div>
            </div>
            <div>
              <div class="text-sm text-gray-500">Client</div>
              <div class="font-medium">Agent {{ test.client.agent_id }}</div>
            </div>
          </div>

          <div v-if="test.metrics" class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div v-if="test.metrics.bps_avg" class="text-center">
              <div class="text-xl font-bold text-green-600">
                {{ formatBps(test.metrics.bps_avg) }}
              </div>
              <div class="text-sm text-gray-500">Throughput</div>
            </div>
            
            <div v-if="test.metrics.retransmits !== null" class="text-center">
              <div class="text-xl font-bold text-orange-600">
                {{ test.metrics.retransmits }}
              </div>
              <div class="text-sm text-gray-500">Retransmits</div>
            </div>
            
            <div v-if="test.metrics.jitter_ms !== null" class="text-center">
              <div class="text-xl font-bold text-blue-600">
                {{ test.metrics.jitter_ms?.toFixed(2) }} ms
              </div>
              <div class="text-sm text-gray-500">Jitter</div>
            </div>
            
            <div v-if="test.metrics.loss_pct !== null" class="text-center">
              <div class="text-xl font-bold text-red-600">
                {{ test.metrics.loss_pct?.toFixed(2) }}%
              </div>
              <div class="text-sm text-gray-500">Packet Loss</div>
            </div>
          </div>

          <div v-if="test.started_at || test.finished_at" class="mt-4 text-sm text-gray-500">
            <span v-if="test.started_at">Started: {{ formatTime(test.started_at) }}</span>
            <span v-if="test.finished_at"> | Finished: {{ formatTime(test.finished_at) }}</span>
          </div>
        </div>
      </div>

      <div v-if="results.tests.length === 0" class="text-center py-8 text-gray-500">
        No test results available yet.
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useApiStore } from '../stores/api'
import StatusBadge from '../components/StatusBadge.vue'

export default {
  name: 'Results',
  components: {
    StatusBadge
  },
  setup() {
    const route = useRoute()
    const apiStore = useApiStore()
    const results = ref(null)
    const loading = ref(false)
    const error = ref('')

    const fetchResults = async () => {
      try {
        loading.value = true
        error.value = ''
        results.value = await apiStore.get(`/v1/exercises/${route.params.exerciseId}/results`)
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to fetch results'
      } finally {
        loading.value = false
      }
    }

    const formatBps = (bps) => {
      if (bps >= 1e9) {
        return `${(bps / 1e9).toFixed(2)} Gbps`
      } else if (bps >= 1e6) {
        return `${(bps / 1e6).toFixed(2)} Mbps`
      } else if (bps >= 1e3) {
        return `${(bps / 1e3).toFixed(2)} Kbps`
      } else {
        return `${bps.toFixed(2)} bps`
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return 'Never'
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    onMounted(() => {
      fetchResults()
    })

    return {
      results,
      loading,
      error,
      formatBps,
      formatTime
    }
  }
}
</script>
