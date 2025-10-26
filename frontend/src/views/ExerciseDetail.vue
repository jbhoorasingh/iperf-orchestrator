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

      <!-- (A) Exercise Summary Bar -->
      <div v-if="aggregateMetrics.successfulTests > 0" class="bg-gradient-to-r from-indigo-500 to-purple-600 shadow rounded-lg p-6 mb-6 text-white">
        <h2 class="text-lg font-semibold mb-4">Exercise Summary</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <div>
            <div class="text-sm opacity-90">Tests</div>
            <div class="text-2xl font-bold">{{ aggregateMetrics.totalTests }}</div>
          </div>
          <div>
            <div class="text-sm opacity-90">Duration (avg)</div>
            <div class="text-2xl font-bold">{{ aggregateMetrics.avgDuration }}s</div>
          </div>
          <div>
            <div class="text-sm opacity-90">Streams Total</div>
            <div class="text-2xl font-bold">{{ aggregateMetrics.totalStreams }}</div>
          </div>
          <div>
            <div class="text-sm opacity-90">Aggregate Throughput (avg)</div>
            <div class="text-2xl font-bold">{{ aggregateMetrics.avgThroughputGbps }} Gbps</div>
          </div>
          <div>
            <div class="text-sm opacity-90">Peak 1-sec Sum</div>
            <div class="text-2xl font-bold">{{ aggregateMetrics.peakThroughputGbps }} Gbps</div>
          </div>
          <div>
            <div class="text-sm opacity-90">Pass Rate</div>
            <div class="text-2xl font-bold">{{ passRate }}</div>
          </div>
          <div v-if="aggregateMetrics.avgCpuHost">
            <div class="text-sm opacity-90">CPU (Host/Remote avg)</div>
            <div class="text-xl font-bold">{{ aggregateMetrics.avgCpuHost }}% / {{ aggregateMetrics.avgCpuRemote }}%</div>
          </div>
        </div>
      </div>

      <!-- (B) Test Comparison Cards -->
      <div v-if="successfulTests.length > 0" class="mb-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Test Results</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="testResult in testResults"
            :key="testResult.test.id"
            class="bg-white shadow rounded-lg p-4 border border-gray-200 hover:border-indigo-400 transition-colors"
          >
            <div class="flex justify-between items-start mb-3">
              <div>
                <h3 class="text-sm font-semibold text-gray-900">
                  Test {{ testResult.test.id }}: {{ getAgentName(testResult.test.server_agent_id) }}:{{ testResult.test.server_port }} ↔ {{ getAgentName(testResult.test.client_agent_id) }}
                </h3>
                <p class="text-xs text-gray-500 mt-1">
                  {{ testResult.parsed ? testResult.parsed.protocol : (testResult.test.udp ? 'UDP' : 'TCP') }},
                  P={{ testResult.test.parallel }},
                  t={{ testResult.test.time_seconds || exercise.duration_seconds }}s
                </p>
              </div>
              <StatusBadge :status="testResult.status" />
            </div>

            <div v-if="testResult.parsed" class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Sum Throughput (avg):</span>
                <span class="font-semibold text-indigo-600">{{ bpsToGbps(testResult.parsed.avgBitsPerSecond) }} Gbps</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Peak 1-sec Sum:</span>
                <span class="font-semibold text-purple-600">{{ bpsToGbps(testResult.peakThroughput) }} Gbps</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Streams:</span>
                <span class="font-medium">{{ testResult.parsed.streams }}</span>
              </div>
              <div v-if="testResult.parsed.cpuHost" class="flex justify-between text-sm">
                <span class="text-gray-600">CPU Host/Remote:</span>
                <span class="font-medium">{{ testResult.parsed.cpuHost.toFixed(1) }}% / {{ testResult.parsed.cpuRemote.toFixed(1) }}%</span>
              </div>

              <!-- Sparkline -->
              <div v-if="testResult.parsed.intervals.length > 0" class="mt-3 pt-3 border-t border-gray-200">
                <p class="text-xs text-gray-500 mb-2">1-sec Throughput (Gbps)</p>
                <Sparkline :data="getSparklineData(testResult.parsed)" :width="250" :height="40" />
              </div>

              <!-- Actions -->
              <div class="flex space-x-2 mt-4">
                <button
                  @click="openTestDetail(testResult)"
                  class="flex-1 bg-indigo-50 text-indigo-700 text-xs px-3 py-2 rounded-md hover:bg-indigo-100 font-medium"
                >
                  View Details
                </button>
                <button
                  @click="downloadJSON(testResult)"
                  class="flex-1 bg-gray-50 text-gray-700 text-xs px-3 py-2 rounded-md hover:bg-gray-100 font-medium"
                >
                  Download JSON
                </button>
              </div>
            </div>

            <div v-else class="text-sm text-gray-500 text-center py-4">
              {{ testResult.status === 'pending' ? 'Test not started' : testResult.status === 'running' ? 'Test in progress...' : 'No results available' }}
            </div>
          </div>
        </div>
      </div>

      <!-- (C) Cross-Test Compare Table -->
      <div v-if="successfulTests.length > 1" class="bg-white shadow rounded-lg p-6 mb-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Cross-Test Comparison</h2>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Test</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Protocol</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Streams</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Sum (Gbps)</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peak 1-sec (Gbps)</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Host CPU</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Remote CPU</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="testResult in successfulTests"
                :key="testResult.test.id"
                class="hover:bg-gray-50 cursor-pointer"
                @click="openTestDetail(testResult)"
              >
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">T{{ testResult.test.id }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                  {{ getAgentName(testResult.test.server_agent_id) }} ↔ {{ getAgentName(testResult.test.client_agent_id) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ testResult.parsed.protocol }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ testResult.parsed.streams }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm font-semibold text-indigo-600">
                  {{ bpsToGbps(testResult.parsed.avgBitsPerSecond) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm font-semibold text-purple-600">
                  {{ bpsToGbps(testResult.peakThroughput) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ testResult.parsed.duration.toFixed(1) }}s</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                  {{ testResult.parsed.cpuHost ? testResult.parsed.cpuHost.toFixed(1) + '%' : 'N/A' }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                  {{ testResult.parsed.cpuRemote ? testResult.parsed.cpuRemote.toFixed(1) + '%' : 'N/A' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tests Section -->
      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-medium text-gray-900">All Tests</h2>
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
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-10"></th>
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
              <template v-for="test in tests" :key="test.id">
                <tr class="hover:bg-gray-50 cursor-pointer" @click="toggleTestExpansion(test.id)">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <svg
                      class="w-5 h-5 transition-transform"
                      :class="{ 'transform rotate-90': expandedTests[test.id] }"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </td>
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

                <!-- Expanded Task Details -->
                <tr v-if="expandedTests[test.id]" class="bg-gray-50">
                  <td colspan="8" class="px-6 py-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <!-- Server Task -->
                      <div class="bg-white rounded-lg p-4 shadow-sm">
                        <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                          <svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                          </svg>
                          Server Task
                        </h4>
                        <div v-if="getServerTask(test)">
                          <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                              <span class="text-gray-600">Task ID:</span>
                              <span class="font-mono text-gray-900">{{ getServerTask(test).id }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Type:</span>
                              <span class="font-mono text-gray-900">{{ getServerTask(test).task_type }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Status:</span>
                              <StatusBadge :status="getServerTask(test).status" />
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Agent:</span>
                              <span class="text-gray-900">{{ getAgentName(getServerTask(test).agent_id) }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Created:</span>
                              <span class="text-gray-900">{{ formatTime(getServerTask(test).created_at) }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Updated:</span>
                              <span class="text-gray-900">{{ formatTime(getServerTask(test).updated_at) }}</span>
                            </div>
                          </div>
                        </div>
                        <div v-else class="text-sm text-gray-500">No server task assigned</div>
                      </div>

                      <!-- Client Task -->
                      <div class="bg-white rounded-lg p-4 shadow-sm">
                        <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                          <svg class="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          Client Task
                        </h4>
                        <div v-if="getClientTask(test)">
                          <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                              <span class="text-gray-600">Task ID:</span>
                              <span class="font-mono text-gray-900">{{ getClientTask(test).id }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Type:</span>
                              <span class="font-mono text-gray-900">{{ getClientTask(test).task_type }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Status:</span>
                              <StatusBadge :status="getClientTask(test).status" />
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Agent:</span>
                              <span class="text-gray-900">{{ getAgentName(getClientTask(test).agent_id) }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Created:</span>
                              <span class="text-gray-900">{{ formatTime(getClientTask(test).created_at) }}</span>
                            </div>
                            <div class="flex justify-between">
                              <span class="text-gray-600">Updated:</span>
                              <span class="text-gray-900">{{ formatTime(getClientTask(test).updated_at) }}</span>
                            </div>
                          </div>

                          <!-- iperf3 Result -->
                          <div v-if="getClientTask(test).result" class="mt-4">
                            <button
                              @click.stop="toggleResultExpansion(test.id)"
                              class="text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center"
                            >
                              <svg
                                class="w-4 h-4 mr-1 transition-transform"
                                :class="{ 'transform rotate-90': expandedResults[test.id] }"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                              </svg>
                              View iperf3 Result
                            </button>
                            <div v-if="expandedResults[test.id]" class="mt-2 bg-gray-900 text-green-400 p-3 rounded-md overflow-x-auto max-h-96 overflow-y-auto">
                              <pre class="text-xs font-mono">{{ JSON.stringify(getClientTask(test).result, null, 2) }}</pre>
                            </div>
                          </div>

                          <!-- Error Message -->
                          <div v-if="getClientTask(test).status === 'failed' && !getClientTask(test).result" class="mt-4 bg-red-50 border border-red-200 rounded-md p-3">
                            <p class="text-sm text-red-700 font-medium">Task failed</p>
                            <p class="text-xs text-red-600 mt-1">No result data available</p>
                          </div>
                        </div>
                        <div v-else class="text-sm text-gray-500">No client task assigned</div>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
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

    <!-- (D) Test Detail Drawer -->
    <div
      v-if="selectedTestDetail"
      class="fixed inset-0 overflow-hidden z-50"
      @click="closeTestDetail"
    >
      <div class="absolute inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
      <div class="fixed inset-y-0 right-0 pl-10 max-w-full flex">
        <div
          class="w-screen max-w-4xl"
          @click.stop
        >
          <div class="h-full flex flex-col bg-white shadow-xl overflow-y-scroll">
            <!-- Header -->
            <div class="px-6 py-6 bg-indigo-600 text-white">
              <div class="flex items-start justify-between">
                <div>
                  <h2 class="text-lg font-medium">
                    Test {{ selectedTestDetail.test.id }} Details
                  </h2>
                  <p class="mt-1 text-sm text-indigo-100">
                    {{ getAgentName(selectedTestDetail.test.server_agent_id) }}:{{ selectedTestDetail.test.server_port }} ↔ {{ getAgentName(selectedTestDetail.test.client_agent_id) }}
                  </p>
                </div>
                <button
                  @click="closeTestDetail"
                  class="ml-3 h-7 w-7 flex items-center justify-center rounded-md text-indigo-200 hover:text-white focus:outline-none"
                >
                  <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 px-6 py-6 space-y-6">
              <!-- Config Section -->
              <div class="bg-gray-50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Test Configuration</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span class="text-gray-600">Protocol:</span>
                    <span class="ml-2 font-medium">{{ selectedTestDetail.parsed?.protocol || (selectedTestDetail.test.udp ? 'UDP' : 'TCP') }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Parallel Streams:</span>
                    <span class="ml-2 font-medium">{{ selectedTestDetail.test.parallel }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Duration:</span>
                    <span class="ml-2 font-medium">{{ selectedTestDetail.parsed?.duration || selectedTestDetail.test.time_seconds || exercise.duration_seconds }}s</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Port:</span>
                    <span class="ml-2 font-medium">{{ selectedTestDetail.test.server_port }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Server Agent:</span>
                    <span class="ml-2 font-medium">{{ getAgentName(selectedTestDetail.test.server_agent_id) }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Client Agent:</span>
                    <span class="ml-2 font-medium">{{ getAgentName(selectedTestDetail.test.client_agent_id) }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Status:</span>
                    <span class="ml-2"><StatusBadge :status="selectedTestDetail.status" /></span>
                  </div>
                </div>
              </div>

              <!-- KPIs Section -->
              <div v-if="selectedTestDetail.parsed" class="bg-white border border-gray-200 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Key Performance Indicators</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div class="text-xs text-gray-500">Avg Throughput</div>
                    <div class="text-xl font-bold text-indigo-600">{{ bpsToGbps(selectedTestDetail.parsed.avgBitsPerSecond) }} Gbps</div>
                  </div>
                  <div>
                    <div class="text-xs text-gray-500">Peak 1-sec</div>
                    <div class="text-xl font-bold text-purple-600">{{ bpsToGbps(selectedTestDetail.peakThroughput) }} Gbps</div>
                  </div>
                  <div>
                    <div class="text-xs text-gray-500">Total Bytes</div>
                    <div class="text-xl font-bold text-gray-900">{{ (selectedTestDetail.parsed.avgBytesTransferred / 1_000_000_000).toFixed(2) }} GB</div>
                  </div>
                  <div v-if="selectedTestDetail.parsed.protocol === 'TCP'">
                    <div class="text-xs text-gray-500">Retransmits</div>
                    <div class="text-xl font-bold text-orange-600">{{ selectedTestDetail.parsed.retransmits }}</div>
                  </div>
                  <div v-if="selectedTestDetail.parsed.cpuHost">
                    <div class="text-xs text-gray-500">CPU Host</div>
                    <div class="text-xl font-bold text-gray-900">{{ selectedTestDetail.parsed.cpuHost.toFixed(1) }}%</div>
                  </div>
                  <div v-if="selectedTestDetail.parsed.cpuRemote">
                    <div class="text-xs text-gray-500">CPU Remote</div>
                    <div class="text-xl font-bold text-gray-900">{{ selectedTestDetail.parsed.cpuRemote.toFixed(1) }}%</div>
                  </div>
                  <div v-if="selectedTestDetail.parsed.jitterMs !== null">
                    <div class="text-xs text-gray-500">Jitter</div>
                    <div class="text-xl font-bold text-gray-900">{{ selectedTestDetail.parsed.jitterMs.toFixed(3) }} ms</div>
                  </div>
                  <div v-if="selectedTestDetail.parsed.lostPercent !== null">
                    <div class="text-xs text-gray-500">Packet Loss</div>
                    <div class="text-xl font-bold text-red-600">{{ selectedTestDetail.parsed.lostPercent.toFixed(2) }}%</div>
                  </div>
                </div>
              </div>

              <!-- Intervals Table -->
              <div v-if="selectedTestDetail.parsed && selectedTestDetail.parsed.intervals.length > 0" class="bg-white border border-gray-200 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Per-Second Intervals</h3>
                <div class="overflow-x-auto max-h-96 overflow-y-auto">
                  <table class="min-w-full divide-y divide-gray-200 text-sm">
                    <thead class="bg-gray-50 sticky top-0">
                      <tr>
                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Interval</th>
                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Throughput (Gbps)</th>
                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Bytes</th>
                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase" v-if="selectedTestDetail.parsed.protocol === 'TCP'">Retransmits</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="(interval, idx) in selectedTestDetail.parsed.intervals" :key="idx" class="hover:bg-gray-50">
                        <td class="px-3 py-2 whitespace-nowrap">{{ interval.start.toFixed(1) }} - {{ interval.end.toFixed(1) }}s</td>
                        <td class="px-3 py-2 whitespace-nowrap font-semibold text-indigo-600">{{ bpsToGbps(interval.bitsPerSecond) }}</td>
                        <td class="px-3 py-2 whitespace-nowrap">{{ (interval.bytes / 1_000_000).toFixed(2) }} MB</td>
                        <td class="px-3 py-2 whitespace-nowrap" v-if="selectedTestDetail.parsed.protocol === 'TCP'">{{ interval.retransmits || 0 }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Raw JSON Section -->
              <div v-if="selectedTestDetail.clientTask && selectedTestDetail.clientTask.result" class="bg-white border border-gray-200 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Raw JSON Result</h3>
                <div class="bg-gray-900 text-green-400 p-4 rounded-md overflow-x-auto max-h-96 overflow-y-auto">
                  <pre class="text-xs font-mono">{{ JSON.stringify(selectedTestDetail.clientTask.result, null, 2) }}</pre>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between">
              <button
                @click="downloadJSON(selectedTestDetail)"
                class="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
              >
                Download JSON
              </button>
              <button
                @click="closeTestDetail"
                class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
              >
                Close
              </button>
            </div>
          </div>
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
import Sparkline from '../components/Sparkline.vue'
import {
  parseIperfResult,
  calculateAggregateMetrics,
  getPeakThroughput,
  formatThroughput,
  bpsToGbps,
  getSparklineData
} from '../utils/iperfParser'

export default {
  name: 'ExerciseDetail',
  components: {
    StatusBadge,
    Sparkline
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
    const expandedTests = ref({})
    const expandedResults = ref({})
    const selectedTestDetail = ref(null)
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
        reservations.value = await apiStore.get('/v1/tasks/ports/reservations')
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

    const getServerTask = (test) => {
      return test.server_task_id ? tasks.value.find(t => t.id === test.server_task_id) : null
    }

    const getClientTask = (test) => {
      return test.client_task_id ? tasks.value.find(t => t.id === test.client_task_id) : null
    }

    const toggleTestExpansion = (testId) => {
      expandedTests.value[testId] = !expandedTests.value[testId]
    }

    const toggleResultExpansion = (testId) => {
      expandedResults.value[testId] = !expandedResults.value[testId]
    }

    const openTestDetail = (testResult) => {
      selectedTestDetail.value = testResult
    }

    const closeTestDetail = () => {
      selectedTestDetail.value = null
    }

    const downloadJSON = (testResult) => {
      if (!testResult.clientTask || !testResult.clientTask.result) return

      const dataStr = JSON.stringify(testResult.clientTask.result, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `test_${testResult.test.id}_result.json`
      link.click()
      URL.revokeObjectURL(url)
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

    // Computed properties for parsed results
    const testResults = computed(() => {
      return tests.value.map(test => {
        const clientTask = getClientTask(test)
        const serverTask = getServerTask(test)

        const result = {
          test,
          clientTask,
          serverTask,
          status: getTestStatus(test),
          parsed: null,
          peakThroughput: 0
        }

        if (clientTask && clientTask.result) {
          result.parsed = parseIperfResult(clientTask.result)
          if (result.parsed) {
            result.peakThroughput = getPeakThroughput(result.parsed)
          }
        }

        return result
      })
    })

    const aggregateMetrics = computed(() => {
      return calculateAggregateMetrics(testResults.value)
    })

    const successfulTests = computed(() => {
      return testResults.value.filter(r => r.status === 'succeeded' && r.parsed)
    })

    const passRate = computed(() => {
      const total = testResults.value.length
      const passed = successfulTests.value.length
      return total > 0 ? `${passed}/${total}` : '0/0'
    })

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
      expandedTests,
      expandedResults,
      selectedTestDetail,
      newTest,
      addTest,
      startExercise,
      stopExercise,
      getTestStatus,
      getServerTask,
      getClientTask,
      toggleTestExpansion,
      toggleResultExpansion,
      openTestDetail,
      closeTestDetail,
      downloadJSON,
      getAgentName,
      formatTime,
      testResults,
      aggregateMetrics,
      successfulTests,
      passRate,
      formatThroughput,
      bpsToGbps,
      getSparklineData
    }
  }
}
</script>
