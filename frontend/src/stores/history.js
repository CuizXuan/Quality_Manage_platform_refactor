import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'api_debug_history'
const MAX_ITEMS = 500
const MAX_DAYS = 30

export const useHistoryStore = defineStore('history', () => {
  const items = ref(loadFromStorage())

  function loadFromStorage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // 过滤超期记录
        const cutoff = Date.now() - MAX_DAYS * 24 * 60 * 60 * 1000
        return parsed.filter(item => new Date(item.createdAt).getTime() > cutoff)
      }
    } catch (e) {
      console.error('Failed to load history:', e)
    }
    return []
  }

  function saveToStorage() {
    try {
      // 限制数量
      const toSave = items.value.slice(0, MAX_ITEMS)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
    } catch (e) {
      console.error('Failed to save history:', e)
    }
  }

  function addItem(record) {
    const item = {
      id: Date.now() + Math.random(),
      createdAt: new Date().toISOString(),
      ...record,
    }
    items.value.unshift(item)
    // 限制数量
    if (items.value.length > MAX_ITEMS) {
      items.value = items.value.slice(0, MAX_ITEMS)
    }
    saveToStorage()
    return item
  }

  function removeItem(id) {
    items.value = items.value.filter(item => item.id !== id)
    saveToStorage()
  }

  function clearAll() {
    items.value = []
    saveToStorage()
  }

  function getFiltered(filters = {}) {
    let result = [...items.value]
    if (filters.method) {
      result = result.filter(item => item.method === filters.method)
    }
    if (filters.status) {
      if (filters.status === 'success') {
        result = result.filter(item => item.statusCode >= 200 && item.statusCode < 300)
      } else if (filters.status === 'error') {
        result = result.filter(item => item.statusCode >= 400 || !item.statusCode)
      }
    }
    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase()
      result = result.filter(item =>
        item.url.toLowerCase().includes(kw) ||
        (item.remark && item.remark.toLowerCase().includes(kw))
      )
    }
    return result
  }

  return {
    items,
    addItem,
    removeItem,
    clearAll,
    getFiltered,
  }
})
