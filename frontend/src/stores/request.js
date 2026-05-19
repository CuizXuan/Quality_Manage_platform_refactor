import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRequestStore = defineStore('request', () => {
  // 当前请求
  const method = ref('GET')
  const url = ref('')
  const headers = ref([{ key: '', value: '', enabled: true }])
  const params = ref([{ key: '', value: '', enabled: true }])
  const body = ref('')
  const bodyType = ref('none') // none, json, form-data, x-www-form-urlencoded, raw
  const fullUrl = ref('') // 完整的 URL（含 query string）

  // 当前响应
  const response = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 重置请求
  function resetRequest() {
    method.value = 'GET'
    url.value = ''
    headers.value = [{ key: '', value: '', enabled: true }]
    params.value = [{ key: '', value: '', enabled: true }]
    body.value = ''
    bodyType.value = 'none'
    fullUrl.value = ''
    response.value = null
    error.value = null
  }

  // 设置请求（从解析器或历史加载）
  function setRequest(req) {
    console.log('[RequestStore] setRequest called with:', req)
    method.value = req.method || 'GET'
    url.value = req.url || ''
    fullUrl.value = req.fullUrl || req.url || ''
    // headers
    if (req.headers && typeof req.headers === 'object') {
      headers.value = Object.entries(req.headers).map(([key, value]) => ({
        key,
        value,
        enabled: true,
      }))
      if (headers.value.length === 0) {
        headers.value = [{ key: '', value: '', enabled: true }]
      }
    }
    // params
    if (req.params && typeof req.params === 'object') {
      params.value = Object.entries(req.params).map(([key, value]) => ({
        key,
        value,
        enabled: true,
      }))
      if (params.value.length === 0) {
        params.value = [{ key: '', value: '', enabled: true }]
      }
    }
    // body
    if (req.body) {
      body.value = typeof req.body === 'string' ? req.body : JSON.stringify(req.body, null, 2)
      bodyType.value = 'json'
    }
    response.value = null
    error.value = null
  }

  return {
    method,
    url,
    headers,
    params,
    body,
    bodyType,
    fullUrl,
    response,
    loading,
    error,
    resetRequest,
    setRequest,
  }
})
