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
        <div v-for="group in navItems" :key="group.label" class="nav-group">
          <button class="nav-group-title" type="button" @click="toggleGroup(group.label)">
            <span class="nav-icon">{{ getMenuIcon(group.icon).symbol }}</span>
            <span class="truncate-cell" :title="group.label">{{ group.label }}</span>
            <ArrowDown class="nav-arrow" :class="{ collapsed: isCollapsed(group.label) }" />
          </button>
          <div v-show="!isCollapsed(group.label)" class="nav-children">
            <RouterLink v-for="item in group.children" :key="item.path" :to="item.path" class="nav-item">
              <span class="nav-icon">{{ getMenuIcon(item.icon).symbol }}</span>
              <span class="truncate-cell" :title="item.label">{{ item.label }}</span>
            </RouterLink>
          </div>
        </div>
      </nav>
    </aside>

    <section class="platform-main">
      <header class="platform-topbar">
        <div>
          <span class="topbar-kicker">SYSTEM SCAFFOLD</span>
          <h1>{{ currentTitle }}</h1>
        </div>
        <div class="topbar-actions">
          <button class="icon-btn" type="button" :title="theme === 'dark' ? '切换浅色主题' : '切换深色主题'" @click="toggleTheme">
            <Sunny v-if="theme === 'dark'" />
            <Moon v-else />
          </button>
          <button class="icon-btn" type="button" :title="`个人中心：${authStore.currentUsername || '用户'}`">
            <User />
          </button>
          <button class="icon-btn danger-btn" type="button" title="退出登录" @click="handleLogout">
            <SwitchButton />
          </button>
        </div>
      </header>

      <main class="workspace">
        <RouterView />
      </main>
    </section>
  </div>
</template>

<script setup>
import { ArrowDown, Moon, Sunny, SwitchButton, User } from '@element-plus/icons-vue'
import { computed, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getMenuIcon } from '@/views/platform/menuIconLibrary'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const theme = ref(localStorage.getItem('platform_theme') || 'dark')
const collapsedGroups = ref(new Set())

const navItems = [
  {
    label: '平台总览',
    icon: 'Monitor',
    children: [{ label: '工作台', path: '/', icon: 'Monitor' }],
  },
  {
    label: '系统管理',
    icon: 'Settings',
    children: [
      { label: '用户管理', path: '/system/users', icon: 'UserRound' },
      { label: '角色管理', path: '/system/roles', icon: 'ShieldCheck' },
      { label: '组织管理', path: '/system/organizations', icon: 'Network' },
      { label: '菜单管理', path: '/system/menus', icon: 'PanelLeft' },
    ],
  },
]

const flatNavItems = computed(() => navItems.flatMap((group) => group.children))
const currentTitle = computed(() => {
  const found = flatNavItems.value.find((item) => item.path === route.path)
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

function isCollapsed(label) {
  return collapsedGroups.value.has(label)
}

function toggleGroup(label) {
  const next = new Set(collapsedGroups.value)
  if (next.has(label)) {
    next.delete(label)
  } else {
    next.add(label)
  }
  collapsedGroups.value = next
}

watchEffect(() => {
  document.documentElement.dataset.platformTheme = theme.value
})
</script>
