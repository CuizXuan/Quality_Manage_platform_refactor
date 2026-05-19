import axios from 'axios'

const request = axios.create({
  baseURL: '/api',   // Vite proxy 会转发到 http://localhost:8000
  timeout: 60000,
})

// 请求拦截器：自动附加认证令牌
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理 401 未授权
request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          const newToken = response.data.access_token
          localStorage.setItem('access_token', newToken)
          sessionStorage.setItem('access_token', newToken)
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return request(originalRequest)
        }
      } catch (refreshError) {
        // 刷新失败，清除 token 并跳转登录
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// 封装常用 REST 方法，Vue 组件直接调用更直观
const http = {
  get<T = any>(url: string, config?: any): Promise<T> {
    return request.get(url, config)
  },
  post<T = any>(url: string, data?: any, config?: any): Promise<T> {
    return request.post(url, data, config)
  },
  put<T = any>(url: string, data?: any, config?: any): Promise<T> {
    return request.put(url, data, config)
  },
  delete<T = any>(url: string, config?: any): Promise<T> {
    return request.delete(url, config)
  },
  patch<T = any>(url: string, data?: any, config?: any): Promise<T> {
    return request.patch(url, data, config)
  },
}

export default http
