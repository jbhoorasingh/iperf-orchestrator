/**
 * Utility functions for parsing iperf3 JSON results
 */

/**
 * Convert bits per second to Gbps
 */
export function bpsToGbps(bps) {
  return bps ? (bps / 1_000_000_000).toFixed(2) : '0.00'
}

/**
 * Convert bytes to GB
 */
export function bytesToGB(bytes) {
  return bytes ? (bytes / 1_000_000_000).toFixed(2) : '0.00'
}

/**
 * Parse iperf3 JSON result and extract key metrics
 * @param {Object} result - The full iperf3 JSON output
 * @returns {Object} Parsed metrics
 */
export function parseIperfResult(result) {
  if (!result || !result.end) {
    return null
  }

  const { start, intervals = [], end } = result

  // Determine if TCP or UDP
  const isUdp = start?.test_start?.protocol === 'UDP'

  // Get summary section based on protocol
  const summary = isUdp ? end.sum : end.sum_sent

  // Basic test info
  const parsed = {
    protocol: isUdp ? 'UDP' : 'TCP',
    duration: end.sum_sent?.seconds || end.sum?.seconds || 0,
    streams: start?.test_start?.num_streams || 1,

    // Connection details
    localHost: start?.connecting_to?.host,
    localPort: start?.connecting_to?.port,

    // Throughput metrics
    avgBitsPerSecond: summary?.bits_per_second || 0,
    avgBytesTransferred: summary?.bytes || 0,

    // TCP specific
    retransmits: end.sum_sent?.retransmits || 0,

    // UDP specific
    jitterMs: end.sum?.jitter_ms || null,
    lostPackets: end.sum?.lost_packets || null,
    lostPercent: end.sum?.lost_percent || null,
    outOfOrder: end.sum?.out_of_order || null,

    // CPU utilization
    cpuHost: end.cpu_utilization_percent?.host_total || null,
    cpuRemote: end.cpu_utilization_percent?.remote_total || null,

    // Intervals for time-series data
    intervals: parseIntervals(intervals),
  }

  return parsed
}

/**
 * Parse interval data for time-series visualization
 * @param {Array} intervals - Array of interval objects from iperf3
 * @returns {Array} Parsed interval data
 */
export function parseIntervals(intervals) {
  if (!intervals || intervals.length === 0) {
    return []
  }

  return intervals.map((interval) => {
    const sum = interval.sum
    const streams = interval.streams || []

    return {
      start: sum.start,
      end: sum.end,
      seconds: sum.seconds,

      // Sum metrics for this interval
      bitsPerSecond: sum.bits_per_second || 0,
      bytes: sum.bytes || 0,
      retransmits: sum.retransmits || 0,

      // Per-stream data
      streams: streams.map((stream) => ({
        socket: stream.socket,
        bitsPerSecond: stream.bits_per_second || 0,
        bytes: stream.bytes || 0,
        retransmits: stream.retransmits || 0,
      }))
    }
  })
}

/**
 * Calculate aggregate metrics across multiple test results
 * @param {Array} testResults - Array of parsed test results
 * @returns {Object} Aggregate metrics
 */
export function calculateAggregateMetrics(testResults) {
  const validResults = testResults.filter(r => r && r.parsed)

  if (validResults.length === 0) {
    return {
      totalTests: 0,
      successfulTests: 0,
      avgDuration: 0,
      totalStreams: 0,
      avgThroughputGbps: 0,
      peakThroughputGbps: 0,
      avgCpuHost: null,
      avgCpuRemote: null,
    }
  }

  const parsedResults = validResults.map(r => r.parsed)

  // Calculate averages
  const avgDuration = parsedResults.reduce((sum, r) => sum + r.duration, 0) / parsedResults.length
  const totalStreams = parsedResults.reduce((sum, r) => sum + r.streams, 0)
  const avgThroughput = parsedResults.reduce((sum, r) => sum + r.avgBitsPerSecond, 0) / parsedResults.length

  // Find peak 1-second throughput across all tests
  let peakThroughput = 0
  parsedResults.forEach(r => {
    if (r.intervals && r.intervals.length > 0) {
      const maxInterval = Math.max(...r.intervals.map(i => i.bitsPerSecond))
      peakThroughput = Math.max(peakThroughput, maxInterval)
    }
  })

  // CPU averages (only from tests that have CPU data)
  const testsWithCpu = parsedResults.filter(r => r.cpuHost !== null)
  const avgCpuHost = testsWithCpu.length > 0
    ? testsWithCpu.reduce((sum, r) => sum + r.cpuHost, 0) / testsWithCpu.length
    : null
  const avgCpuRemote = testsWithCpu.length > 0
    ? testsWithCpu.reduce((sum, r) => sum + r.cpuRemote, 0) / testsWithCpu.length
    : null

  return {
    totalTests: testResults.length,
    successfulTests: validResults.length,
    avgDuration: Math.round(avgDuration),
    totalStreams,
    avgThroughputGbps: parseFloat(bpsToGbps(avgThroughput)),
    peakThroughputGbps: parseFloat(bpsToGbps(peakThroughput)),
    avgCpuHost: avgCpuHost !== null ? avgCpuHost.toFixed(1) : null,
    avgCpuRemote: avgCpuRemote !== null ? avgCpuRemote.toFixed(1) : null,
  }
}

/**
 * Get peak 1-second throughput for a single test
 * @param {Object} parsed - Parsed iperf result
 * @returns {number} Peak throughput in bps
 */
export function getPeakThroughput(parsed) {
  if (!parsed || !parsed.intervals || parsed.intervals.length === 0) {
    return parsed?.avgBitsPerSecond || 0
  }

  return Math.max(...parsed.intervals.map(i => i.bitsPerSecond))
}

/**
 * Format throughput for display
 * @param {number} bps - Bits per second
 * @returns {string} Formatted string (e.g., "59.8 Gbps")
 */
export function formatThroughput(bps) {
  const gbps = bps / 1_000_000_000
  if (gbps >= 1) {
    return `${gbps.toFixed(2)} Gbps`
  }
  const mbps = bps / 1_000_000
  if (mbps >= 1) {
    return `${mbps.toFixed(2)} Mbps`
  }
  const kbps = bps / 1_000
  return `${kbps.toFixed(2)} Kbps`
}

/**
 * Get data points for sparkline chart
 * @param {Object} parsed - Parsed iperf result
 * @returns {Array} Array of throughput values (in Gbps) for each interval
 */
export function getSparklineData(parsed) {
  if (!parsed || !parsed.intervals || parsed.intervals.length === 0) {
    return []
  }

  return parsed.intervals.map(i => parseFloat(bpsToGbps(i.bitsPerSecond)))
}
