import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import client from '@/api/client'

function readToken(key) {
  return localStorage.getItem(key) || sessionStorage.getItem(key)
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(readToken('access_token'))
  const refreshToken = ref(readToken('refresh_token'))
  const user = ref(null)
  const loading = ref(false)
  const error = ref('')
  const remember = ref(!!localStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!accessToken.value)
  const currentUsername = computed(() => user.value?.display_name || user.value?.username || '')
  const permissions = computed(() => user.value?.permissions || [])

  function saveTokens(access, refresh) {
    const storage = remember.value ? localStorage : sessionStorage
    clearTokens()
    storage.setItem('access_token', access)
    storage.setItem('refresh_token', refresh)
    accessToken.value = access
    refreshToken.value = refresh
  }

  function clearTokens() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
  }

  async function login(username, password, rememberMe = false) {
    loading.value = true
    error.value = ''
    remember.value = rememberMe
    try {
      const response = await client.post('/api/auth/login', { username, password })
      saveTokens(response.data.access_token, response.data.refresh_token)
      await fetchUserInfo()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(username, email, password) {
    loading.value = true
    error.value = ''
    try {
      const response = await client.post('/api/auth/register', { username, email, password })
      saveTokens(response.data.access_token, response.data.refresh_token)
      await fetchUserInfo()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchUserInfo() {
    if (!accessToken.value) return null
    try {
      const response = await client.get('/api/auth/me')
      user.value = response.data
      return user.value
    } catch (err) {
      if (err.response?.status === 401 && refreshToken.value) {
        const refreshed = await refreshAccessToken()
        if (refreshed) return fetchUserInfo()
      }
      logout()
      return null
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) return false
    try {
      const response = await client.post('/api/auth/refresh', {
        refresh_token: refreshToken.value,
      })
      saveTokens(response.data.access_token, response.data.refresh_token)
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    clearTokens()
  }

  async function changePassword(oldPassword, newPassword) {
    loading.value = true
    error.value = ''
    try {
      await client.post('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '密码修改失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  if (accessToken.value) {
    fetchUserInfo()
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    isAuthenticated,
    currentUsername,
    permissions,
    login,
    register,
    fetchUserInfo,
    refreshAccessToken,
    logout,
    changePassword,
  }
})

