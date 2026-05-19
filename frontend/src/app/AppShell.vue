<template>
  <div class="platform-shell" :class="themeClass">
    <aside class="platform-sidebar">
      <div class="brand">
        <div class="brand-mark">Q</div>
        <div>
          <strong>Quality Platform</strong>
          <span>Command Center</span>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <section class="platform-main">
      <header class="platform-topbar">
        <div>
          <span class="topbar-kicker">SYSTEM SCAFFOLD</span>
          <h1>{{ currentTitle }}</h1>
        </div>
        <div class="topbar-actions">
          <button class="theme-toggle" type="button" @click="toggleTheme">
            {{ theme === 'dark' ? '浅色' : '深色' }}
          </button>
          <div class="user-chip">
            <span>{{ authStore.currentUsername || '用户' }}</span>
            <button type="button" @click="handleLogout">退出</button>
          </div>
        </div>
      </header>

      <main class="workspace">
        <RouterView />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const theme = ref(localStorage.getItem('platform_theme') || 'dark')

const navItems = [
  { label: '工作台', path: '/', icon: '▦' },
  { label: '用户管理', path: '/system/users', icon: '◎' },
  { label: '角色管理', path: '/system/roles', icon: '◇' },
  { label: '组织管理', path: '/system/organizations', icon: '⌘' },
  { label: '菜单管理', path: '/system/menus', icon: '☰' },
]

const currentTitle = computed(() => {
  const found = navItems.find((item) => item.path === route.path)
  return found?.label || '工作台'
})

const themeClass = computed(() => `theme-${theme.value}`)

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('platform_theme', theme.value)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

watchEffect(() => {
  document.documentElement.dataset.platformTheme = theme.value
})
</script>

