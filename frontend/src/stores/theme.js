import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // 默认深色主题
  const isDark = ref(true)
  
  // 初始化时从 localStorage 读取
  function init() {
    const saved = localStorage.getItem('cyber-theme')
    if (saved !== null) {
      isDark.value = saved === 'dark'
    }
  }
  
  // 切换主题
  function toggle() {
    isDark.value = !isDark.value
  }
  
  // 设置特定主题
  function setTheme(dark) {
    isDark.value = dark
  }
  
  // 监听变化，保存到 localStorage
  watch(isDark, (val) => {
    localStorage.setItem('cyber-theme', val ? 'dark' : 'light')
  })
  
  return {
    isDark,
    init,
    toggle,
    setTheme,
  }
})
