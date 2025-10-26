<template>
  <span 
    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
    :class="badgeClass"
  >
    {{ status }}
  </span>
</template>

<script>
export default {
  name: 'StatusBadge',
  props: {
    status: {
      type: String,
      required: true
    }
  },
  computed: {
    badgeClass() {
      const classes = {
        'online': 'bg-green-100 text-green-800',
        'offline': 'bg-red-100 text-red-800',
        'succeeded': 'bg-green-100 text-green-800',
        'failed': 'bg-red-100 text-red-800',
        'running': 'bg-yellow-100 text-yellow-800',
        'queued': 'bg-purple-100 text-purple-800',
        'pending': 'bg-gray-100 text-gray-800',
        'accepted': 'bg-blue-100 text-blue-800',
        'canceled': 'bg-gray-100 text-gray-800',
        'timed_out': 'bg-orange-100 text-orange-800'
      }
      return classes[this.status] || 'bg-gray-100 text-gray-800'
    }
  }
}
</script>
