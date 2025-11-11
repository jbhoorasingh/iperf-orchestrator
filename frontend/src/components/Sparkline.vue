<template>
  <canvas ref="chartRef" :width="width" :height="height"></canvas>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'Sparkline',
  props: {
    data: {
      type: Array,
      required: true,
      default: () => []
    },
    serverData: {
      type: Array,
      default: null
    },
    width: {
      type: Number,
      default: 200
    },
    height: {
      type: Number,
      default: 40
    },
    color: {
      type: String,
      default: '#6366f1'
    },
    serverColor: {
      type: String,
      default: '#3b82f6'
    }
  },
  setup(props) {
    const chartRef = ref(null)
    let chartInstance = null

    const createChart = () => {
      if (!chartRef.value || props.data.length === 0) return

      // Destroy existing chart if any
      if (chartInstance) {
        chartInstance.destroy()
      }

      const ctx = chartRef.value.getContext('2d')

      // Build datasets array
      const datasets = [
        {
          label: 'Client',
          data: props.data,
          borderColor: props.color,
          backgroundColor: props.color + '20',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 0,
        }
      ]

      // Add server dataset if available
      if (props.serverData && props.serverData.length > 0) {
        datasets.push({
          label: 'Server',
          data: props.serverData,
          borderColor: props.serverColor,
          backgroundColor: props.serverColor + '20',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 0,
        })
      }

      // Use the longer dataset for labels
      const maxLength = Math.max(props.data.length, props.serverData?.length || 0)

      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: Array.from({ length: maxLength }, (_, i) => i + 1),
          datasets
        },
        options: {
          responsive: false,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: props.serverData && props.serverData.length > 0
            }
          },
          scales: {
            x: {
              display: false
            },
            y: {
              display: false,
              beginAtZero: true
            }
          }
        }
      })
    }

    onMounted(() => {
      createChart()
    })

    watch(() => [props.data, props.serverData], () => {
      createChart()
    }, { deep: true })

    return {
      chartRef
    }
  }
}
</script>
