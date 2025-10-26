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

      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: props.data.map((_, i) => i + 1),
          datasets: [{
            data: props.data,
            borderColor: props.color,
            backgroundColor: props.color + '20',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 0,
          }]
        },
        options: {
          responsive: false,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: false
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

    watch(() => props.data, () => {
      createChart()
    }, { deep: true })

    return {
      chartRef
    }
  }
}
</script>
