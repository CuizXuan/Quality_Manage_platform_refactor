import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useToastStore } from './toast'

const STORAGE_KEY = 'api_debug_collections'

export const useCollectionStore = defineStore('collection', () => {
  const collections = ref(loadFromStorage())

  function loadFromStorage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : []
    } catch (e) {
      console.error('Failed to load collections:', e)
      return []
    }
  }

  function saveToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collections.value))
    } catch (e) {
      console.error('Failed to save collections:', e)
    }
  }

  function createCollection(name) {
    const col = {
      id: Date.now(),
      name,
      children: [],
      requests: [],
      createdAt: new Date().toISOString(),
    }
    collections.value.push(col)
    saveToStorage()
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '创建成功',
      message: `集合"${name}"已创建`,
      duration: 3000
    })
    return col
  }

  function deleteCollection(id) {
    const col = collections.value.find(c => c.id === id)
    collections.value = collections.value.filter(col => col.id !== id)
    saveToStorage()
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '删除成功',
      message: '集合已删除',
      duration: 3000
    })
  }

  function renameCollection(id, name) {
    const col = collections.value.find(c => c.id === id)
    if (col) {
      col.name = name
      saveToStorage()
      const toast = useToastStore()
      toast.addToast({
        id: Date.now(),
        type: 'success',
        title: '重命名成功',
        message: `已重命名为"${name}"`,
        duration: 3000
      })
    }
  }

  function addRequest(collectionId, request) {
    const col = collections.value.find(c => c.id === collectionId)
    if (col) {
      col.requests.push({
        id: Date.now(),
        ...request,
        createdAt: new Date().toISOString(),
      })
      saveToStorage()
    }
  }

  function removeRequest(collectionId, requestId) {
    const col = collections.value.find(c => c.id === collectionId)
    if (col) {
      col.requests = col.requests.filter(r => r.id !== requestId)
      saveToStorage()
    }
  }

  return {
    collections,
    createCollection,
    deleteCollection,
    renameCollection,
    addRequest,
    removeRequest,
  }
})
