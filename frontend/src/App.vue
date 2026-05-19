<template>
  <div class="app-layout" :class="themeClass">
    <template v-if="showAppLayout">
      <DigitalRain v-if="isDark" />
      <AppHeader :is-dark="isDark" @toggle-theme="toggleTheme" @set-theme="setTheme" />
      <div class="app-body">
        <Sidebar v-if="showSidebar" :is-dark="isDark" @load-request="onLoadRequest" />
        <main class="app-main" :class="{ 'no-sidebar': !showSidebar }">
          <router-view />
        </main>
      </div>
      <StatusBar />
    </template>
    <template v-else>
      <router-view />
    </template>
    <CyberToast />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/common/AppHeader.vue'
import Sidebar from './components/common/Sidebar.vue'
import StatusBar from './components/common/StatusBar.vue'
import DigitalRain from './components/common/DigitalRain.vue'

const route = useRoute()
const isDark = ref(true)

onMounted(() => {
  const saved = localStorage.getItem('cyber-theme')
  if (saved !== null) {
    isDark.value = saved === 'dark'
  }
  updateThemeClass()
})

// 控制是否显示侧边栏
const SIDEBAR_ROUTES = ['Dashboard', 'Cases', 'Scenarios', 'Environments', 'History', 'Datasets', 'Schedules', 'MockRules', 'Reports', 'Repositories', 'Defects', 'QualityGates', 'Projects', 'Users', 'TeamManage', 'AssetCenter', 'AILab', 'TrafficLoadTest', 'ChaosStudio', 'TestDataFactory']
const showSidebar = computed(() => SIDEBAR_ROUTES.includes(route.name))

// 控制是否显示应用布局（登录页不显示）
const showAppLayout = computed(() => {
  return route.name !== 'Login'
})

function updateThemeClass() {
  if (isDark.value) {
    document.documentElement.classList.add('theme-dark')
    document.documentElement.classList.remove('theme-light')
  } else {
    document.documentElement.classList.add('theme-light')
    document.documentElement.classList.remove('theme-dark')
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('cyber-theme', isDark.value ? 'dark' : 'light')
  updateThemeClass()
}

function setTheme(theme) {
  isDark.value = theme === 'dark'
  localStorage.setItem('cyber-theme', isDark.value ? 'dark' : 'light')
  updateThemeClass()
}

const themeClass = computed(() => {
  return isDark.value ? 'theme-dark' : 'theme-light'
})

function onLoadRequest() {
  // Sidebar 加载请求后，可以在这里做后续处理
}

// 监听路由变化
watch(route, () => {
  updateThemeClass()
})
</script>

<style>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  position: relative;
}

.app-body {
  display: flex;
  flex: 1;
  margin-top: var(--header-height);
  margin-bottom: 28px;
  position: relative;
  z-index: 1;
}

.app-main {
  flex: 1;
  margin-left: var(--sidebar-width);
  overflow-y: auto;
  padding: 16px;
}

.app-main.no-sidebar {
  margin-left: 0;
}
</style>
