// Phase 4 - 认证状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useToastStore } from './toast'

const API_BASE = '/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State - 根据 remember 选择存储位置
  const getStorage = (key, defaultValue) => {
    // 先检查 localStorage，再检查 sessionStorage
    return localStorage.getItem(key) || sessionStorage.getItem(key) || defaultValue
  }

  const accessToken = ref(getStorage('access_token', null))
  const refreshToken = ref(getStorage('refresh_token', null))
  const remember = ref(!!localStorage.getItem('access_token') || !!sessionStorage.getItem('access_token'))
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 辅助函数：存储 token
  const saveTokens = (access, refresh) => {
    if (remember.value) {
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
    } else {
      sessionStorage.setItem('access_token', access)
      sessionStorage.setItem('refresh_token', refresh)
    }
  }

  // 辅助函数：清除 token
  const clearTokens = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
  }

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => {
    if (!user.value) return false
    return user.value.roles?.includes('SuperAdmin') ||
           user.value.roles?.includes('TenantAdmin')
  })
  const currentUsername = computed(() => user.value?.username || '')

  // Actions
  async function login(username, password, rememberMe = false) {
    loading.value = true
    error.value = null
    remember.value = rememberMe
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (!response.ok) {
        let errMsg = '请求失败'
        try {
          const data = await response.json()
          errMsg = data.detail || data.message || errMsg
        } catch {
          // 非 JSON 响应（text/plain），直接用 status text
          errMsg = response.statusText || errMsg
        }
        throw new Error(errMsg)
      }

      const data = await response.json()
      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token

      // 根据 remember 选择存储位置
      saveTokens(data.access_token, data.refresh_token)

      // 获取用户信息
      await fetchUserInfo()

      // 显示成功 Toast
      const toastStore = useToastStore()
      toastStore.addToast({
        id: Date.now(),
        type: 'success',
        title: '登录成功',
        message: `欢迎回来 ${username}`,
        duration: 3500
      })

      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(username, email, password) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
      })

      if (!response.ok) {
        let errMsg = '请求失败'
        try {
          const data = await response.json()
          errMsg = data.detail || data.message || errMsg
        } catch {
          // 非 JSON 响应（text/plain），直接用 status text
          errMsg = response.statusText || errMsg
        }
        throw new Error(errMsg)
      }

      const data = await response.json()
      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token

      // 根据 remember 选择存储位置
      saveTokens(data.access_token, data.refresh_token)

      // 获取用户信息
      await fetchUserInfo()

      // 显示成功 Toast
      const toastStore = useToastStore()
      toastStore.addToast({
        id: Date.now(),
        type: 'success',
        title: '注册成功',
        message: '账号创建成功',
        duration: 3500
      })

      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchUserInfo() {
    if (!accessToken.value) return null
    
    try {
      const response = await fetch(`${API_BASE}/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken.value}`
        }
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token 过期，尝试刷新
          await refreshAccessToken()
          if (accessToken.value) {
            return fetchUserInfo()
          }
        }
        throw new Error('获取用户信息失败')
      }
      
      user.value = await response.json()
      return user.value
    } catch (err) {
      error.value = err.message
      return null
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) return false
    
    try {
      const response = await fetch(`${API_BASE}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken.value })
      })
      
      if (!response.ok) {
        throw new Error('刷新令牌失败')
      }
      
      const data = await response.json()
      accessToken.value = data.access_token
      saveTokens(data.access_token, refreshToken.value)
      return true
    } catch (err) {
      error.value = err.message
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

  // 初始化时获取用户信息
  if (accessToken.value) {
    fetchUserInfo()
  }

  return {
    // State
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
    currentUsername,
    // Actions
    login,
    register,
    logout,
    fetchUserInfo,
    refreshAccessToken
  }
})
