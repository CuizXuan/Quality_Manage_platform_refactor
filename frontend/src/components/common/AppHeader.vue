<template>
  <header class="app-header">
    <div class="header-left">
      <span class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">CYBER<span class="highlight">API</span></span>
      </span>

      <!-- 导航滚动区域 -->
      <div class="nav-scroll-container">
        <!-- 左滚动按钮 -->
        <button
          v-if="showLeftArrow"
          class="nav-scroll-btn left"
          @click="scrollNav(-1)"
          title="向左滚动"
        >◀</button>

        <nav ref="navRef" class="main-nav">
          <!-- 动态渲染菜单 -->
          <template v-for="item in visibleMenuItems" :key="item.name">
            <!-- 有子菜单的 -->
            <div
              v-if="item.children && item.children.length"
              class="nav-item nav-dropdown"
              :class="{ active: isActiveGroup(item) }"
              @mouseenter="onDropdownEnter(item.name)"
              @mouseleave="onDropdownLeave(item.name)"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span>{{ item.name }}</span>
              <span class="dropdown-arrow">▼</span>
              <div
                class="nav-dropdown-menu"
                :class="{ 'is-open': showNavDropdown }"
                @mouseenter="onMenuEnter"
                @mouseleave="onMenuLeave"
              >
                <router-link
                  v-for="child in item.children"
                  :key="child.path"
                  :to="child.path"
                  class="dropdown-item"
                  :class="{ active: $route.path === child.path }"
                >
                  <span>{{ child.icon }}</span>
                  <span>{{ child.name }}</span>
                </router-link>
              </div>
            </div>
            <!-- 无子菜单的 -->
            <router-link
              v-else
              :to="item.path"
              class="nav-item"
              :class="{ active: $route.path === item.path }"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span>{{ item.name }}</span>
            </router-link>
          </template>

          <!-- 系统管理（固定在最后） -->
          <div
            class="nav-item nav-dropdown"
            :class="{ active: isSysActive }"
            @mouseenter="onDropdownEnter('sys')"
            @mouseleave="onDropdownLeave('sys')"
          >
            <span class="nav-icon">⚙</span>
            <span>系统管理</span>
            <span class="dropdown-arrow">▼</span>
            <div
              class="nav-dropdown-menu"
              :class="{ 'is-open': showNavDropdown }"
              @mouseenter="onMenuEnter"
              @mouseleave="onMenuLeave"
            >
              <router-link to="/menu-manage" class="dropdown-item" :class="{ active: $route.path === '/menu-manage' }">
                <span>📋</span><span>菜单管理</span>
              </router-link>
              <router-link to="/ai-model-config" class="dropdown-item" :class="{ active: $route.path === '/ai-model-config' }">
                <span>🤖</span><span>AI模型配置</span>
              </router-link>
              <router-link to="/users" class="dropdown-item" :class="{ active: $route.path === '/users' }">
                <span>👥</span><span>用户管理</span>
              </router-link>
              <router-link to="/projects" class="dropdown-item" :class="{ active: $route.path === '/projects' }">
                <span>📁</span><span>项目管理</span>
              </router-link>
              <router-link to="/assets" class="dropdown-item" :class="{ active: $route.path === '/assets' }">
                <span>📦</span><span>资产管理</span>
              </router-link>
              <div class="dropdown-divider"></div>
              <router-link to="/audit" class="dropdown-item" :class="{ active: $route.path === '/audit' }">
                <span>📋</span><span>审计日志</span>
              </router-link>
            </div>
          </div>
        </nav>

        <!-- 右滚动按钮 -->
        <button
          v-if="showRightArrow"
          class="nav-scroll-btn right"
          @click="scrollNav(1)"
          title="向右滚动"
        >▶</button>
      </div>
    </div>

    <div class="header-right">
      <!-- Custom Environment Dropdown -->
      <div class="env-switch" v-click-outside="closeEnvDropdown">
        <button class="env-trigger" @click="toggleEnvDropdown">
          <span class="env-label">环境</span>
          <span class="env-value">
            <span class="env-dot" :class="currentEnv"></span>
            <span class="env-name">{{ currentEnv.toUpperCase() }}</span>
          </span>
          <svg class="env-arrow" :class="{ open: showEnvDropdown }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <Transition name="env-dropdown">
          <div v-if="showEnvDropdown" class="env-dropdown">
            <button
              v-for="env in envOptions"
              :key="env.value"
              class="env-option"
              :class="{ active: currentEnv === env.value }"
              @click="selectEnv(env.value)"
            >
              <span class="env-option-dot" :class="env.value"></span>
              <span class="env-option-name">{{ env.label }}</span>
              <svg v-if="currentEnv === env.value" class="env-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </button>
          </div>
        </Transition>
      </div>

      <router-link to="/settings" class="icon-btn" title="设置">⚙</router-link>

      <!-- AI User Control Dropdown -->
      <div class="user-control" v-click-outside="closeDropdown">
        <button class="user-trigger" @click="toggleDropdown">
          <span class="user-avatar">
            <span class="avatar-orb"></span>
          </span>
          <span class="user-info">
            <span class="user-name">{{ authStore.currentUsername || '用户' }}</span>
            <span class="user-workspace">AI 工作区</span>
          </span>
          <span class="dropdown-arrow" :class="{ open: showDropdown }">▼</span>
        </button>

        <Transition name="dropdown">
          <div v-if="showDropdown" class="user-dropdown">
            <div class="dropdown-header">
              <div class="dropdown-user-info">
                <span class="dropdown-user-name">{{ authStore.currentUsername || '用户' }}</span>
                <span class="dropdown-user-email">workspace@cyberapi.io</span>
              </div>
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" @click="goToProfile">
              <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              <span>个人中心</span>
            </button>
            <button class="dropdown-item" @click="goToWorkspaceSettings">
              <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="9" y1="3" x2="9" y2="21"></line>
              </svg>
              <span>工作区设置</span>
            </button>
            <button class="dropdown-item" @click="openThemePanel">
              <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
              </svg>
              <span>主题外观</span>
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item logout-item" @click="handleLogout">
              <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              <span>结束会话</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Logout Confirm Modal -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="showLogoutConfirm" class="modal-overlay" @click.self="showLogoutConfirm = false">
            <div class="confirm-modal">
              <div class="confirm-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
              </div>
              <h3 class="confirm-title">确定要结束当前工作区会话？</h3>
              <p class="confirm-message">您的工作已保存，随时可以重新登录。</p>
              <div class="confirm-actions">
                <button class="confirm-btn cancel" @click="showLogoutConfirm = false">取消</button>
                <button class="confirm-btn end-session" @click="confirmLogout">结束会话</button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Theme Panel -->
      <Teleport to="body">
        <Transition name="panel">
          <div v-if="showThemePanel" class="theme-panel-overlay" @click.self="closeThemePanel">
            <div class="theme-panel">
              <div class="theme-panel-header">
                <h3>主题外观</h3>
                <button class="theme-panel-close" @click="closeThemePanel">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
              <div class="theme-panel-content">
                <div class="theme-section">
                  <div class="theme-section-title">外观模式</div>
                  <div class="theme-options">
                    <button
                      class="theme-option"
                      :class="{ active: isDark }"
                      @click="setTheme('dark')"
                    >
                      <span class="theme-option-icon dark-icon">☾</span>
                      <span>深色</span>
                    </button>
                    <button
                      class="theme-option"
                      :class="{ active: !isDark }"
                      @click="setTheme('light')"
                    >
                      <span class="theme-option-icon light-icon">☀</span>
                      <span>浅色</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggle-theme', 'set-theme'])
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// User dropdown state
const showDropdown = ref(false)

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function closeDropdown() {
  showDropdown.value = false
}

// Environment dropdown state
const showEnvDropdown = ref(false)
const currentEnv = ref('dev')
const envOptions = [
  { value: 'dev', label: 'DEV' },
  { value: 'test', label: 'TEST' },
  { value: 'prod', label: 'PROD' }
]

function toggleEnvDropdown() {
  showEnvDropdown.value = !showEnvDropdown.value
}

function closeEnvDropdown() {
  showEnvDropdown.value = false
}

function selectEnv(env) {
  currentEnv.value = env
  closeEnvDropdown()
}

// Click outside directive
const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (event) => {
      if (!el.contains(event.target)) {
        binding.value()
      }
    }
    document.addEventListener('click', el._clickOutside)
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutside)
  }
}

// Logout confirm state
const showLogoutConfirm = ref(false)

function handleLogout() {
  closeDropdown()
  showLogoutConfirm.value = true
}

function confirmLogout() {
  showLogoutConfirm.value = false
  authStore.logout()
  router.push('/login')
}

// Navigation functions
function goToProfile() {
  closeDropdown()
  router.push('/profile')
}

function goToWorkspaceSettings() {
  closeDropdown()
  router.push('/workspace-settings')
}

// Theme panel state
const showThemePanel = ref(false)

function openThemePanel() {
  closeDropdown()
  showThemePanel.value = true
}

function closeThemePanel() {
  showThemePanel.value = false
}

function setTheme(theme) {
  emit('set-theme', theme)
  closeThemePanel()
}

const navRef = ref(null)
const showLeftArrow = ref(false)
const showRightArrow = ref(false)

// ==================== 菜单配置 ====================
// 默认菜单配置（系统管理固定在最后）
const DEFAULT_MENU = [
  { name: '终端', icon: '⌘', path: '/' },
  { name: '用例', icon: '☰', path: '/cases' },
  { name: '场景', icon: '⚙', path: '/scenarios' },
  { name: '环境', icon: '◈', path: '/environments' },
  { name: '日志', icon: '▤', path: '/history' },
  { name: '数据集', icon: '◫', path: '/datasets' },
  { name: '定时', icon: '◷', path: '/schedules' },
  { name: 'Mock', icon: '◇', path: '/mock-rules' },
  { name: '报告', icon: '▦', path: '/reports' },
  { name: '代码质量', icon: '⚡', path: '/repositories' },
  { name: '缺陷管理', icon: '🐛', path: '/defects' },
  { name: '质量门禁', icon: '⚖', path: '/quality-gates' },
  { name: 'AI分析', icon: '🤖', path: '/ai-analysis' },
  { name: '大盘', icon: '📊', path: '/quality-dashboard' },
  { name: 'AI实验室', icon: '✨', path: '/ai-lab' },
  { name: '压测', icon: '⚡', path: '/load-test' },
  { name: '混沌', icon: '🧪', path: '/chaos' },
  { name: '数据', icon: '🗄', path: '/test-data' },
  { name: '插件市场', icon: '🛒', path: '/marketplace' },
]

// 带分组的菜单配置（示例）
const GROUPED_MENU = [
  {
    name: '测试工具',
    icon: '🧰',
    children: [
      { name: '用例', icon: '☰', path: '/cases' },
      { name: '场景', icon: '⚙', path: '/scenarios' },
      { name: 'Mock', icon: '◇', path: '/mock-rules' },
      { name: '报告', icon: '▦', path: '/reports' },
    ]
  },
  {
    name: '质量保障',
    icon: '🔍',
    children: [
      { name: '代码质量', icon: '⚡', path: '/repositories' },
      { name: '缺陷管理', icon: '🐛', path: '/defects' },
      { name: '质量门禁', icon: '⚖', path: '/quality-gates' },
      { name: 'AI分析', icon: '🤖', path: '/ai-analysis' },
    ]
  },
  {
    name: '高级测试',
    icon: '🚀',
    children: [
      { name: 'AI实验室', icon: '✨', path: '/ai-lab' },
      { name: '压测', icon: '⚡', path: '/load-test' },
      { name: '混沌', icon: '🧪', path: '/chaos' },
      { name: '数据', icon: '🗄', path: '/test-data' },
    ]
  },
  {
    name: '基础功能',
    icon: '⌘',
    children: [
      { name: '终端', icon: '⌘', path: '/' },
      { name: '环境', icon: '◈', path: '/environments' },
      { name: '日志', icon: '▤', path: '/history' },
      { name: '数据集', icon: '◫', path: '/datasets' },
      { name: '定时', icon: '◷', path: '/schedules' },
    ]
  },
]

// 加载菜单配置（优先从 localStorage 读取）
function loadMenuConfig() {
  try {
    const saved = localStorage.getItem('nav_menu_config')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.warn('Failed to load menu config:', e)
  }
  return null
}

// 当前菜单（默认或配置的）
const menuConfig = loadMenuConfig()
const navMenu = computed(() => {
  if (menuConfig) {
    // 配置模式：把系统管理的 children 动态加入
    return menuConfig
  }
  return DEFAULT_MENU
})

// 用于渲染的菜单项（系统管理之外的）
const visibleMenuItems = computed(() => navMenu.value)

// ==================== 滚动逻辑 ====================
const NAV_ITEM_APPROX_WIDTH = 80 // 每个菜单项预估宽度

function updateScrollButtons() {
  if (!navRef.value) return
  const el = navRef.value
  const hasOverflow = el.scrollWidth > el.clientWidth + 2
  showRightArrow.value = hasOverflow && el.scrollLeft + el.clientWidth < el.scrollWidth - 2
  showLeftArrow.value = el.scrollLeft > 2
}

function scrollNav(direction) {
  if (!navRef.value) return
  const scrollAmount = NAV_ITEM_APPROX_WIDTH * 3
  navRef.value.scrollBy({ left: direction * scrollAmount, behavior: 'smooth' })
  setTimeout(updateScrollButtons, 300)
}

// ==================== 下拉菜单逻辑 ====================
const showNavDropdown = ref(false)
let showTimer = null
let hideTimer = null
const SHOW_DELAY = 100     // 鼠标进入后延迟显示
const HIDE_DELAY = 200     // 鼠标离开后延迟隐藏（防止间隙闪烁）

function onDropdownEnter(name) {
  clearTimeout(hideTimer)
  clearTimeout(showTimer)
  showTimer = setTimeout(() => {
    showNavDropdown.value = true
  }, SHOW_DELAY)
}

function onDropdownLeave(name) {
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
  hideTimer = setTimeout(() => {
    showNavDropdown.value = false
  }, HIDE_DELAY)
}

function onMenuEnter() {
  clearTimeout(hideTimer)
  clearTimeout(showTimer)
  showNavDropdown.value = true
}

function onMenuLeave() {
  clearTimeout(showTimer)
  hideTimer = setTimeout(() => {
    showNavDropdown.value = false
  }, HIDE_DELAY)
}

function isActiveGroup(item) {
  return (item.children || []).some(c => c.path === route.path)
}

const isSysActive = computed(() => {
  const sysPaths = ['/menu-manage', '/users', '/projects', '/assets', '/audit']
  return sysPaths.includes(route.path)
})

// ==================== 生命周期 ====================
let resizeObserver = null

onMounted(() => {
  nextTick(() => {
    updateScrollButtons()
    resizeObserver = new ResizeObserver(() => {
      updateScrollButtons()
    })
    if (navRef.value) {
      resizeObserver.observe(navRef.value)
    }
  })
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid var(--border-default);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0;
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 24px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-family: var(--font-title);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--text-primary);
}

.logo-text .highlight {
  color: var(--primary);
}

/* ==================== 导航滚动容器 ==================== */
.nav-scroll-container {
  display: flex;
  align-items: center;
  position: relative;
}

.main-nav {
  display: flex;
  gap: 2px;
  overflow-x: visible;
  scroll-behavior: smooth;
  scrollbar-width: none;
  -ms-overflow-style: none;
  max-width: calc(100vw - 400px);
}

.main-nav::-webkit-scrollbar {
  display: none;
}

.main-nav,
.nav-scroll-container {
  overflow: visible !important;
}

/* ==================== 滚动按钮 ==================== */
.nav-scroll-btn {
  flex-shrink: 0;
  width: 24px;
  height: 32px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  transition: all 0.2s;
  z-index: 10;
}

.nav-scroll-btn:hover {
  opacity: 1;
  background: var(--bg-card-hover);
  border-color: var(--border-hover);
}

.nav-scroll-btn.left {
  border-radius: var(--radius-sm) 0 0 var(--radius-sm);
  margin-right: 1px;
}

.nav-scroll-btn.right {
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  margin-left: 1px;
}

/* ==================== 导航项 ==================== */
.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  position: relative;
  overflow: visible;
  transition: all var(--transition-fast);
  white-space: nowrap;
  cursor: pointer;
  flex-shrink: 0;
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-card);
}

.nav-item.active {
  color: var(--primary);
  background: var(--primary-muted);
}

.nav-icon {
  font-size: 13px;
}

.dropdown-arrow {
  font-size: 8px;
  opacity: 0.7;
}

/* ==================== 下拉菜单 ==================== */
.nav-dropdown {
  position: relative;
}

.nav-dropdown-menu {
  display: none;
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 180px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 9999;
  padding: 4px 0;
  overflow: hidden;
}

.nav-dropdown-menu.is-open {
  display: block;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.15s;
  cursor: pointer;
}

.dropdown-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.dropdown-item.active {
  background: var(--primary-muted);
  color: var(--primary);
}

.dropdown-divider {
  height: 1px;
  background: var(--divider);
  margin: 4px 0;
}

/* ==================== 右侧区域 ==================== */
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* ==================== Custom Environment Dropdown ==================== */
.env-switch {
  position: relative;
}

.env-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--text-primary);
}

.env-trigger:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-hover);
}

.env-label {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--text-tertiary);
  padding-right: 4px;
  border-right: 1px solid var(--border-default);
}

.env-value {
  display: flex;
  align-items: center;
  gap: 6px;
}

.env-name {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.env-arrow {
  width: 14px;
  height: 14px;
  color: var(--text-tertiary);
  transition: transform 0.2s ease;
  margin-left: 2px;
}

.env-arrow.open {
  transform: rotate(180deg);
}

/* Environment Dropdown Panel */
.env-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 140px;
  background: var(--glass-bg);
  backdrop-filter: blur(24px);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xl);
  padding: 6px;
  z-index: 9999;
}

.env-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 36px;
  padding: 0 10px;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.env-option:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.env-option.active {
  background: var(--primary-muted);
  color: var(--primary);
}

.env-option-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.env-option-dot.dev {
  background: var(--success);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
}

.env-option-dot.test {
  background: var(--warning);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
}

.env-option-dot.prod {
  background: var(--error);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.env-option-name {
  flex: 1;
  text-align: left;
  letter-spacing: 0.5px;
}

.env-check {
  width: 14px;
  height: 14px;
  color: var(--primary);
}

/* Environment dot indicator */
.env-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.env-dot.dev {
  background: var(--success);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
}

.env-dot.test {
  background: var(--warning);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
}

.env-dot.prod {
  background: var(--error);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
}

/* Environment dropdown animation */
.env-dropdown-enter-active {
  transition: all 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}

.env-dropdown-leave-active {
  transition: all 0.12s ease;
}

.env-dropdown-enter-from {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

.env-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.icon-btn {
  color: var(--text-secondary);
  font-size: 18px;
  text-decoration: none;
  padding: 6px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
}

.icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-card);
  border-color: var(--border-default);
}

/* ==================== AI User Control ==================== */
.user-control {
  position: relative;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--text-primary);
}

.user-trigger:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-1px);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-orb {
  display: block;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #5B8CFF, #7C4DFF);
  box-shadow: 0 0 20px rgba(91, 140, 255, 0.25);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}

.user-workspace {
  font-size: 10px;
  color: var(--text-tertiary);
  line-height: 1.2;
}

.dropdown-arrow {
  font-size: 8px;
  color: var(--text-tertiary);
  transition: transform 0.2s ease;
  margin-left: 4px;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

/* ==================== User Dropdown Menu ==================== */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: rgba(15, 18, 28, 0.95);
  backdrop-filter: blur(24px);
  border: 1px solid var(--border-default);
  border-radius: 20px;
  box-shadow: var(--shadow-xl);
  padding: 8px 0;
  z-index: 9999;
  overflow: hidden;
}

/* 浅色主题下更不透明的背景 */
.theme-light .user-dropdown {
  background: rgba(255, 255, 255, 0.95);
}

.dropdown-header {
  padding: 12px 14px;
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.dropdown-user-email {
  font-size: 12px;
  color: var(--text-tertiary);
}

.dropdown-divider {
  height: 1px;
  background: var(--divider);
  margin: 4px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 40px;
  padding: 0 14px;
  background: none;
  border: none;
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.dropdown-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  opacity: 0.7;
  flex-shrink: 0;
}

.dropdown-item:hover .dropdown-icon {
  opacity: 1;
}

.logout-item {
  color: rgba(255, 120, 120, 0.82);
}

.logout-item:hover {
  background: rgba(255, 80, 80, 0.08);
  color: rgba(255, 160, 160, 0.96);
}

.logout-item:hover .dropdown-icon {
  opacity: 1;
}

/* ==================== Dropdown Animation ==================== */
.dropdown-enter-active {
  transition: all 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}

.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(6px) scale(0.98);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ==================== Logout Confirm Modal ==================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 18, 28, 0.88);
  backdrop-filter: blur(32px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

.confirm-modal {
  background: rgba(15, 18, 28, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 32px;
  max-width: 360px;
  width: 90%;
  text-align: center;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
}

.confirm-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 20px;
  color: rgba(255, 120, 120, 0.82);
}

.confirm-icon svg {
  width: 100%;
  height: 100%;
}

.confirm-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
  line-height: 1.4;
}

.confirm-message {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 24px;
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.confirm-btn {
  flex: 1;
  height: 40px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.confirm-btn.cancel {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.confirm-btn.cancel:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.confirm-btn.end-session {
  background: rgba(255, 80, 80, 0.12);
  color: rgba(255, 160, 160, 0.96);
  border: 1px solid rgba(255, 80, 80, 0.2);
}

.confirm-btn.end-session:hover {
  background: rgba(255, 80, 80, 0.2);
}

/* ==================== Modal Animation ==================== */
.modal-enter-active {
  transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}

.modal-leave-active {
  transition: all 0.15s ease;
}

.modal-enter-from {
  opacity: 0;
}

.modal-enter-from .confirm-modal {
  transform: scale(0.95) translateY(10px);
}

.modal-leave-to {
  opacity: 0;
}

.modal-leave-to .confirm-modal {
  transform: scale(0.95);
}

/* ==================== Theme Panel ==================== */
.theme-panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 18, 28, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding-top: 72px;
  padding-right: 24px;
  z-index: 99998;
}

.theme-panel {
  width: 320px;
  background: rgba(15, 18, 28, 0.92);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.theme-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.theme-panel-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.theme-panel-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.06);
  border: none;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-panel-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.theme-panel-close svg {
  width: 14px;
  height: 14px;
}

.theme-panel-content {
  padding: 16px 20px;
}

.theme-section {
  margin-bottom: 16px;
}

.theme-section:last-child {
  margin-bottom: 0;
}

.theme-section-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.theme-options {
  display: flex;
  gap: 8px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-option:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.theme-option.active {
  background: rgba(91, 140, 255, 0.12);
  border-color: rgba(91, 140, 255, 0.3);
  color: var(--primary);
}

.theme-option-icon {
  font-size: 20px;
  line-height: 1;
}

.dark-icon {
  color: var(--text-secondary);
}

.theme-option.active .dark-icon {
  color: var(--primary);
}

.light-icon {
  color: var(--warning);
}

.theme-option.active .light-icon {
  color: var(--primary);
}

/* ==================== Panel Animation ==================== */
.panel-enter-active {
  transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}

.panel-leave-active {
  transition: all 0.15s ease;
}

.panel-enter-from {
  opacity: 0;
}

.panel-enter-from .theme-panel {
  transform: translateY(-10px) scale(0.98);
}

.panel-leave-to {
  opacity: 0;
}

.panel-leave-to .theme-panel {
  transform: translateY(-5px);
}
</style>
