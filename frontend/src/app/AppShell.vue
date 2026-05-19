<template>
  <el-container class="app-shell">
    <el-aside :width="sidebarWidth" class="app-sidebar">
      <div class="brand" :class="{ 'brand--collapsed': isCollapse }">
        <div class="brand__mark">Q</div>
        <div v-if="!isCollapse" class="brand__text">
          <strong>Quality Platform</strong>
          <span>Command Center</span>
        </div>
      </div>

      <el-menu
        :collapse="isCollapse"
        :default-active="activeMenu"
        :router="true"
        :unique-opened="true"
        background-color="var(--bg-sidebar)"
        text-color="var(--text-primary)"
        active-text-color="var(--el-color-primary)"
        class="menu-sidebar"
      >
        <template v-for="item in menuList" :key="item.path">
          <el-menu-item v-if="!item.children?.length" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
          <el-sub-menu v-else :index="item.path">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
              <el-icon><component :is="child.icon" /></el-icon>
              <template #title>{{ child.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <el-container direction="vertical" class="app-content">
      <el-header height="var(--header-height)" class="app-header">
        <div class="header-left">
          <el-button text :icon="FoldIcon" @click="toggleCollapse" />
          <el-breadcrumb separator="/" class="header-breadcrumb">
            <el-breadcrumb-item v-for="crumb in breadcrumbs" :key="crumb">{{ crumb }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <div class="environment-switch">
            <span>环境</span>
            <el-select v-model="currentEnvironment" size="small" :teleported="true">
              <el-option label="本地环境" value="local" />
              <el-option label="开发环境" value="dev" />
              <el-option label="测试环境" value="test" />
              <el-option label="预生产" value="staging" />
            </el-select>
          </div>
          <el-button text :icon="isDark ? Sunny : Moon" @click="toggleTheme" />
          <el-button text :icon="User" :title="`个人中心：${authStore.currentUsername || '用户'}`" />
          <el-button text type="danger" :icon="SwitchButton" title="退出登录" @click="handleLogout" />
        </div>
      </el-header>

      <el-main class="app-main" :class="{ 'app-main--full': isFullBleed }">
        <RouterView v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </RouterView>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {
  Connection,
  CopyDocument,
  Document,
  DocumentChecked,
  Expand,
  Fold,
  Menu as MenuIcon,
  Monitor,
  Moon,
  Setting,
  SwitchButton,
  Sunny,
  User,
  Folder,
  List,
  Warning,
  CircleCheck,
  Bell,
  Key,
  VideoPlay,
  TrendCharts,
} from '@element-plus/icons-vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isDark = ref((localStorage.getItem('theme') || 'dark') === 'dark')
const isCollapse = ref(localStorage.getItem('sidebar_collapse') === 'true')
const currentEnvironment = ref(localStorage.getItem('platform_environment') || 'local')

const menuList = [
  { title: '工作台', icon: Monitor, path: '/' },
  {
    title: '工具',
    icon: MenuIcon,
    path: '/tools',
    children: [
      { title: '终端调试台', icon: Connection, path: '/terminal' },
      { title: '用例管理', icon: DocumentChecked, path: '/case' },
    ],
  },
  {
    title: '测试执行',
    icon: VideoPlay,
    path: '/execution',
    children: [
      { title: '场景管理', icon: Folder, path: '/scenario' },
      { title: '执行历史', icon: List, path: '/scenario/executions' },
    ],
  },
  {
    title: '质量中心',
    icon: CircleCheck,
    path: '/quality',
    children: [
      { title: '报告中心', icon: Document, path: '/report' },
      { title: '缺陷中心', icon: Warning, path: '/defect' },
      { title: '门禁管理', icon: Key, path: '/quality-gate' },
    ],
  },
  {
    title: 'AI 中枢',
    icon: TrendCharts,
    path: '/ai',
    children: [
      { title: '模型配置', icon: Setting, path: '/ai/config' },
      { title: 'Prompt模板', icon: Document, path: '/ai/templates' },
      { title: '变体生成', icon: CopyDocument, path: '/ai/variant-generator' },
      { title: '断言生成', icon: CircleCheck, path: '/ai/assertion-generator' },
      { title: '失败归因', icon: Warning, path: '/ai/failure-analyzer' },
      { title: '报告总结', icon: Document, path: '/ai/report-summarizer' },
      { title: '采纳历史', icon: List, path: '/ai/suggestion-history' },
    ],
  },
  {
    title: '系统管理',
    icon: Setting,
    path: '/system',
    children: [
      { title: '用户管理', icon: User, path: '/system/users' },
      { title: '角色管理', icon: Document, path: '/system/roles' },
      { title: '组织管理', icon: Monitor, path: '/system/organizations' },
      { title: '菜单管理', icon: MenuIcon, path: '/system/menus' },
    ],
  },
]

const flatMenu = computed(() => {
  return menuList.flatMap((item) => item.children?.length ? item.children : [item])
})

const activeMenu = computed(() => {
  const normalizedPath = route.path === '/' ? '/' : route.path.replace(/\/$/, '')
  const exact = flatMenu.value.find((item) => item.path === normalizedPath)
  if (exact) return exact.path
  const parent = flatMenu.value.find((item) => normalizedPath.startsWith(`${item.path}/`))
  return parent?.path || '/'
})

const breadcrumbs = computed(() => {
  const current = flatMenu.value.find((item) => item.path === activeMenu.value)
  const parent = menuList.find((item) => item.children?.some((child) => child.path === current?.path))
  if (!current) return ['工作台']
  return parent ? [parent.title, current.title] : [current.title]
})

const sidebarWidth = computed(() => isCollapse.value ? 'var(--sidebar-width-collapsed)' : 'var(--sidebar-width)')
const FoldIcon = computed(() => isCollapse.value ? Expand : Fold)
const isFullBleed = computed(() => route.name === 'Terminal')

function toggleTheme() {
  setTheme(!isDark.value)
}

function setTheme(dark) {
  isDark.value = dark
  document.documentElement.classList.toggle('dark', dark)
  localStorage.setItem('theme', dark ? 'dark' : 'light')
}

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
  localStorage.setItem('sidebar_collapse', String(isCollapse.value))
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  setTheme(isDark.value)
})

watch(currentEnvironment, (value) => {
  localStorage.setItem('platform_environment', value)
})
</script>

<style scoped>
.app-shell {
  height: 100vh;
  background: var(--bg-page);
  color: var(--text-primary);
}

.app-sidebar {
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  transition: width 0.2s ease;
  overflow: hidden;
}

.brand {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  height: var(--header-height);
  padding: 0 var(--spacing-md);
}

.brand--collapsed {
  justify-content: center;
  padding: 0;
}

.brand__mark {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  border-radius: var(--border-radius-base);
  color: var(--text-inverse);
  background: var(--brand-gradient);
  font-weight: 900;
}

.brand__text {
  min-width: 0;
}

.brand__text strong,
.brand__text span {
  display: block;
}

.brand__text strong {
  color: var(--text-strong);
  font-size: 14px;
  line-height: 1.2;
}

.brand__text span {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.menu-sidebar {
  padding: 0 var(--spacing-sm);
}

.app-content {
  min-width: 0;
}

.app-header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: center;
  padding: 0 var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-container);
}

.header-left,
.header-right,
.environment-switch {
  display: flex;
  align-items: center;
}

.header-left {
  min-width: 0;
  gap: var(--spacing-sm);
}

.header-right {
  gap: var(--spacing-sm);
}

.header-breadcrumb {
  min-width: 0;
}

.environment-switch {
  gap: var(--spacing-sm);
  color: var(--text-secondary);
  font-size: 13px;
}

.environment-switch .el-select {
  width: 132px;
}

.app-main {
  min-height: 0;
  padding: var(--spacing-md);
  background: var(--bg-page);
  overflow: auto;
}

.app-main--full {
  padding: 0;
  overflow: hidden;
}
</style>
