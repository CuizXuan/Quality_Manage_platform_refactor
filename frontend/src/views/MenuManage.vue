<template>
  <div class="menu-manage">
    <div class="page-header">
      <h1 class="page-title">菜单管理</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="resetToDefault">恢复默认</button>
        <button class="btn-secondary" @click="showGroupDialog = true">+ 添加分组</button>
        <button class="btn-primary" @click="saveConfig">💾 保存配置</button>
      </div>
    </div>

    <!-- 预览区域 -->
    <div class="preview-section">
      <h3>顶部导航预览</h3>
      <div class="nav-preview">
        <div class="preview-logo">⚡ CYBER<span class="highlight">API</span></div>
        <div class="preview-nav">
          <template v-for="(item, idx) in editedMenu" :key="idx">
            <!-- 分组 -->
            <div
              v-if="item.children && item.children.length"
              class="preview-dropdown"
            >
              <div class="preview-nav-item" @click="toggleGroupPreview(idx)">
                <span>{{ item.icon }}</span>
                <span>{{ item.name }}</span>
                <span class="arrow">▼</span>
              </div>
              <div v-if="openPreviewGroup === idx" class="preview-dropdown-menu">
                <div
                  v-for="child in item.children"
                  :key="child.path"
                  class="preview-dropdown-item"
                >
                  {{ child.icon }} {{ child.name }}
                </div>
              </div>
            </div>
            <!-- 普通项 -->
            <div v-else class="preview-nav-item">
              <span>{{ item.icon }}</span>
              <span>{{ item.name }}</span>
            </div>
          </template>
          <!-- 系统管理固定 -->
          <div class="preview-dropdown">
            <div class="preview-nav-item" @click="toggleGroupPreview('sys')">
              <span>⚙</span><span>系统管理</span><span class="arrow">▼</span>
            </div>
            <div v-if="openPreviewGroup === 'sys'" class="preview-dropdown-menu">
              <div class="preview-dropdown-item">📋 菜单管理</div>
              <div class="preview-dropdown-item">👥 用户管理</div>
              <div class="preview-dropdown-item">📁 项目管理</div>
              <div class="preview-dropdown-item">📦 资产管理</div>
            </div>
          </div>
        </div>
      </div>
      <p class="preview-hint">* 系统管理为固定菜单，不可配置</p>
    </div>

    <!-- 编辑区域 -->
    <div class="edit-section">
      <div class="edit-header">
        <h3>菜单配置</h3>
        <button class="btn-secondary btn-small" @click="addStandaloneItem">
          + 添加菜单项
        </button>
      </div>

      <!-- 分组列表 -->
      <div v-for="(group, gi) in editedMenu" :key="gi" class="group-card">
        <div class="group-header" v-if="group.children && group.children.length">
          <div class="group-info">
            <input
              v-model="group.name"
              class="group-name-input"
              placeholder="分组名称"
            />
            <input
              v-model="group.icon"
              class="group-icon-input"
              placeholder="图标"
            />
          </div>
          <div class="group-actions">
            <button class="btn-secondary btn-small" @click="addItemToGroup(gi)">+ 添加项</button>
            <button class="btn-danger btn-small" @click="removeGroup(gi)">删除分组</button>
          </div>
        </div>

        <!-- 分组内的菜单项 -->
        <div v-if="group.children && group.children.length" class="group-items">
          <div
            v-for="(item, ii) in group.children"
            :key="ii"
            class="menu-item-row"
          >
            <input v-model="item.icon" class="item-icon" placeholder="图标" />
            <input v-model="item.name" class="item-name" placeholder="名称" />
            <input v-model="item.path" class="item-path" placeholder="/path" />
            <button class="btn-danger btn-small" @click="removeItem(gi, ii)">✕</button>
          </div>
        </div>

        <!-- 独立菜单项（没有 children 的分组，实际是独立项） -->
        <div v-else class="group-items">
          <div class="menu-item-row">
            <input v-model="group.icon" class="item-icon" placeholder="图标" />
            <input v-model="group.name" class="item-name" placeholder="名称" />
            <input v-model="group.path" class="item-path" placeholder="/path" />
            <button class="btn-danger btn-small" @click="removeGroup(gi)">✕</button>
          </div>
        </div>
      </div>

      <!-- 提示 -->
      <div class="config-tip">
        <p>💡 <strong>提示：</strong></p>
        <ul>
          <li>拖拽可调整菜单顺序（功能开发中）</li>
          <li>分组模式下，同一分组内的菜单会收纳为下拉菜单</li>
          <li>不加分组的菜单项会平铺显示</li>
          <li>保存后顶部导航会立即更新</li>
        </ul>
      </div>
    </div>

    <!-- 添加分组弹窗 -->
    <div v-if="showGroupDialog" class="modal-overlay" @click.self="showGroupDialog = false">
      <div class="modal">
        <div class="modal-header">
          <h2>添加分组</h2>
          <button class="btn-close" @click="showGroupDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>分组名称 *</label>
            <input v-model="newGroup.name" type="text" placeholder="例如：测试工具" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="newGroup.icon" type="text" placeholder="例如：🧰" />
          </div>
          <div class="form-group">
            <label>添加菜单项</label>
            <div v-for="(item, idx) in newGroup.children" :key="idx" class="menu-item-row">
              <input v-model="item.icon" class="item-icon" placeholder="图标" />
              <input v-model="item.name" class="item-name" placeholder="名称" />
              <input v-model="item.path" class="item-path" placeholder="/path" />
              <button class="btn-danger btn-small" @click="newGroup.children.splice(idx, 1)">✕</button>
            </div>
            <button class="btn-secondary btn-small" @click="newGroup.children.push({ icon: '', name: '', path: '' })">
              + 添加项
            </button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showGroupDialog = false">取消</button>
          <button class="btn-primary" @click="addGroup" :disabled="!newGroup.name">添加</button>
        </div>
      </div>
    </div>

    <!-- 保存成功提示 -->
    <div v-if="showSaved" class="toast">✅ 配置已保存，导航菜单已更新</div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const editedMenu = ref([])
const openPreviewGroup = ref(null)
const showGroupDialog = ref(false)
const showSaved = ref(false)

// 新建分组
const newGroup = reactive({
  name: '',
  icon: '',
  children: [{ icon: '', name: '', path: '' }],
})

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

onMounted(() => {
  loadConfig()
})

function loadConfig() {
  try {
    const saved = localStorage.getItem('nav_menu_config')
    if (saved) {
      editedMenu.value = JSON.parse(saved)
      return
    }
  } catch (e) {}
  // 默认使用分组模式
  editedMenu.value = JSON.parse(JSON.stringify(GROUPED_MENU))
}

function resetToDefault() {
  if (confirm('确定恢复默认配置？这将覆盖当前配置。')) {
    editedMenu.value = JSON.parse(JSON.stringify(GROUPED_MENU))
    localStorage.removeItem('nav_menu_config')
  }
}

function addStandaloneItem() {
  editedMenu.value.push({ icon: '📌', name: '新菜单', path: '/new', children: [] })
}

function addGroup() {
  if (!newGroup.name) return
  editedMenu.value.push(JSON.parse(JSON.stringify(newGroup)))
  newGroup.name = ''
  newGroup.icon = ''
  newGroup.children = [{ icon: '', name: '', path: '' }]
  showGroupDialog.value = false
}

function addItemToGroup(gi) {
  editedMenu.value[gi].children.push({ icon: '', name: '', path: '' })
}

function removeGroup(gi) {
  editedMenu.value.splice(gi, 1)
}

function removeItem(gi, ii) {
  editedMenu.value[gi].children.splice(ii, 1)
}

function saveConfig() {
  // 清理空项
  const cleaned = editedMenu.value.filter(item => {
    if (item.children && item.children.length) {
      item.children = item.children.filter(c => c.name && c.path)
      return item.children.length > 0 || item.name
    }
    return item.name && item.path
  })

  localStorage.setItem('nav_menu_config', JSON.stringify(cleaned))
  showSaved.value = true
  setTimeout(() => { showSaved.value = false }, 3000)
  // 提示用户刷新页面或自动重载
  setTimeout(() => {
    window.location.reload()
  }, 1000)
}

function toggleGroupPreview(idx) {
  openPreviewGroup.value = openPreviewGroup.value === idx ? null : idx
}
</script>

<style scoped>
.menu-manage {
  padding: 24px;
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 预览 */
.preview-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.preview-section h3 {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.nav-preview {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--bg-panel);
  border: 1px solid var(--neon-cyan);
  border-radius: 8px;
  padding: 8px 12px;
  overflow-x: auto;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
}

.preview-logo {
  font-family: var(--font-title);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 2px;
  color: #fff;
  text-shadow: 0 0 8px var(--neon-cyan);
  margin-right: 20px;
  white-space: nowrap;
}

.preview-logo .highlight {
  color: var(--neon-cyan);
}

.preview-nav {
  display: flex;
  gap: 2px;
  align-items: center;
}

.preview-nav-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.preview-nav-item:hover {
  background: rgba(0, 255, 255, 0.05);
  color: var(--neon-cyan);
  border-color: rgba(0, 255, 255, 0.3);
}

.arrow {
  font-size: 8px;
  opacity: 0.7;
}

.preview-dropdown {
  position: relative;
}

.preview-dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 140px;
  background: var(--bg-panel);
  border: 1px solid var(--neon-cyan);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  z-index: 100;
  padding: 4px 0;
}

.preview-dropdown-item {
  padding: 6px 12px;
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  gap: 6px;
  align-items: center;
}

.preview-dropdown-item:hover {
  background: rgba(0, 255, 255, 0.1);
  color: var(--neon-cyan);
}

.preview-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 8px 0 0;
}

/* 编辑区域 */
.edit-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.edit-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.group-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-default);
}

.group-info {
  display: flex;
  gap: 8px;
  align-items: center;
}

.group-name-input,
.group-icon-input {
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.group-icon-input {
  width: 50px;
  text-align: center;
}

.group-actions {
  display: flex;
  gap: 8px;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.item-icon {
  width: 50px;
  padding: 6px 8px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  text-align: center;
}

.item-name {
  width: 140px;
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.item-path {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.config-tip {
  margin-top: 20px;
  padding: 16px;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.config-tip p {
  margin: 0 0 8px;
}

.config-tip ul {
  margin: 0;
  padding-left: 20px;
}

.config-tip li {
  margin-bottom: 4px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-panel);
  border: 1px solid var(--neon-cyan);
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-default);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-default);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  box-sizing: border-box;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--neon-cyan);
  color: #000;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  z-index: 9999;
  box-shadow: 0 4px 20px rgba(0, 255, 255, 0.5);
}

/* Buttons */
.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  padding: 10px 20px;
  background: var(--bg-secondary);
  color: var(--neon-cyan);
  border: 1px solid var(--neon-cyan);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(0, 255, 255, 0.1);
}

.btn-danger {
  padding: 6px 10px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.2);
}

.btn-small {
  padding: 4px 10px;
  font-size: 12px;
}
</style>
