import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const isAuthenticated = computed(() => !!token.value)

  const login = async (username, password) => {
    try {
      const response = await axios.post('/v1/auth/login', {
        username,
        password
      })
      
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
      
      // Set default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      axios.defaults.headers.common['X-API-Version'] = '1'
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Login failed' 
      }
    }
  }

  const logout = () => {
    token.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  // Initialize axios headers if token exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    axios.defaults.headers.common['X-API-Version'] = '1'
  }

  return {
    token,
    isAuthenticated,
    login,
    logout
  }
})
