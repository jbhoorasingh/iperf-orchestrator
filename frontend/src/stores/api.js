import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'
import router from '../router'

// Setup axios response interceptor for handling 401 errors
let isInterceptorSetup = false

const setupAxiosInterceptor = () => {
  if (isInterceptorSetup) return

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      // Handle 401 Unauthorized - token expired or invalid
      if (error.response && error.response.status === 401) {
        const authStore = useAuthStore()

        // Only logout if we're not already on the login page
        if (router.currentRoute.value.name !== 'Login') {
          authStore.logout()
          router.push({ name: 'Login' })
        }
      }
      return Promise.reject(error)
    }
  )

  isInterceptorSetup = true
}

// Helper function to extract meaningful error messages from API responses
const getErrorMessage = (error) => {
  if (!error.response) {
    return 'Network error - please check your connection'
  }

  const data = error.response.data

  // Handle structured error responses with detail object
  if (data?.detail) {
    // If detail is an object with message property
    if (typeof data.detail === 'object' && data.detail.message) {
      return data.detail.message
    }
    // If detail is a string
    if (typeof data.detail === 'string') {
      return data.detail
    }
    // If detail is an array (validation errors)
    if (Array.isArray(data.detail)) {
      return data.detail.map(err => err.msg || err.message || JSON.stringify(err)).join(', ')
    }
  }

  // Fallback to message property
  if (data?.message) {
    return data.message
  }

  // Fallback based on status code
  const status = error.response.status
  const statusMessages = {
    400: 'Bad request - please check your input',
    401: 'Unauthorized - please log in',
    403: 'Forbidden - you don\'t have permission',
    404: 'Resource not found',
    409: 'Conflict - resource already exists',
    422: 'Validation error - please check your input',
    500: 'Server error - please try again later',
    503: 'Service unavailable - please try again later'
  }

  return statusMessages[status] || `Request failed with status ${status}`
}

export const useApiStore = defineStore('api', () => {
  // Setup interceptor on first use
  setupAxiosInterceptor()

  const loading = ref(false)
  const error = ref(null)

  const setLoading = (value) => {
    loading.value = value
  }

  const setError = (err) => {
    error.value = err
  }

  const clearError = () => {
    error.value = null
  }

  // API methods
  const get = async (url) => {
    try {
      setLoading(true)
      clearError()
      const response = await axios.get(url)
      return response.data
    } catch (err) {
      const message = getErrorMessage(err)
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const post = async (url, data) => {
    try {
      setLoading(true)
      clearError()
      const response = await axios.post(url, data)
      return response.data
    } catch (err) {
      const message = getErrorMessage(err)
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const put = async (url, data) => {
    try {
      setLoading(true)
      clearError()
      const response = await axios.put(url, data)
      return response.data
    } catch (err) {
      const message = getErrorMessage(err)
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const del = async (url) => {
    try {
      setLoading(true)
      clearError()
      const response = await axios.delete(url)
      return response.data
    } catch (err) {
      const message = getErrorMessage(err)
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    error,
    setLoading,
    setError,
    clearError,
    get,
    post,
    put,
    del
  }
})
