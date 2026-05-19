<template>
  <div class="dashboard">
    <!-- 标签页 -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key; loadDashboards()"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 仪表盘选择器 -->
    <div class="dashboard-selector">
      <select v-model="selectedDashboardId" @change="loadDashboardDetails" class="dashboard-select">
        <option v-for="db in dashboards" :key="db.id" :value="db.id">
          {{ db.name }} {{ db.is_default ? '(默认)' : '' }}
        </option>
      </select>
      <button class="btn-primary" @click="showCreateDialog = true">新建仪表盘</button>
      <button v-if="currentDashboard" class="btn-secondary" @click="showWidgetDialog = true">
        + 添加组件
      </button>
    </div>

    <!-- 仪表盘视图 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="currentDashboard" class="dashboard-grid">
      <div
        v-for="widget in widgets"
        :key="widget.id"
        class="widget-card"
        :style="getWidgetStyle(widget)"
      >
        <div class="widget-header">
          <span class="widget-title">{{ widget.title }}</span>
          <button class="btn-icon" @click="deleteWidget(widget)">×</button>
        </div>
        <div class="widget-content">
          <component :is="getWidgetComponent(widget.widget_type)" :config="widget.config" />
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="widgets.length === 0" class="empty-state">
        <p>暂无组件</p>
        <button class="btn-primary" @click="showWidgetDialog = true">添加第一个组件</button>
      </div>
    </div>

    <!-- 创建仪表盘弹窗 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog">
        <h2>新建仪表盘</h2>
        <form @submit.prevent="createDashboard">
          <div class="form-group">
            <label>仪表盘名称</label>
            <input v-model="newDashboard.name" type="text" placeholder="例如：我的质量大盘" required />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="newDashboard.type">
              <option value="personal">个人</option>
              <option value="project">项目</option>
              <option value="tenant">租户</option>
            </select>
          </div>
          <div class="dialog-actions">
            <button type="button" class="btn-secondary" @click="showCreateDialog = false">取消</button>
            <button type="submit" class="btn-primary">创建</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 添加组件弹窗 -->
    <div v-if="showWidgetDialog" class="dialog-overlay" @click.self="showWidgetDialog = false">
      <div class="dialog">
        <h2>添加组件</h2>
        <div class="widget-types">
          <div 
            v-for="wt in widgetTypes" 
            :key="wt.type"
            class="widget-type-card"
            @click="selectWidgetType(wt.type)"
          >
            <span class="wt-icon">{{ wt.icon }}</span>
            <span class="wt-name">{{ wt.name }}</span>
          </div>
        </div>
        <form v-if="selectedWidgetType" @submit.prevent="addWidget" style="margin-top: 16px;">
          <div class="form-group">
            <label>组件标题</label>
            <input v-model="newWidget.title" type="text" placeholder="例如：执行趋势" required />
          </div>
          <div class="form-group">
            <label>配置 (JSON)</label>
            <textarea v-model="newWidget.config" rows="4" placeholder='{"metric": "total_cases"}'></textarea>
          </div>
          <div class="dialog-actions">
            <button type="button" class="btn-secondary" @click="showWidgetDialog = false">取消</button>
            <button type="submit" class="btn-primary">添加</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const tabs = [
  { key: 'personal', label: '个人' },
  { key: 'project', label: '项目' },
  { key: 'tenant', label: '租户' }
]
const currentTab = ref('personal')
const dashboards = ref([])
const selectedDashboardId = ref(null)
const currentDashboard = ref(null)
const widgets = ref([])
const loading = ref(false)

const showCreateDialog = ref(false)
const newDashboard = ref({ name: '', type: 'personal' })

const showWidgetDialog = ref(false)
const widgetTypes = [
  { type: 'metric_card', name: '指标卡片', icon: '📊' },
  { type: 'line_chart', name: '折线图', icon: '📈' },
  { type: 'bar_chart', name: '柱状图', icon: '📉' },
  { type: 'pie_chart', name: '饼图', icon: '🥧' },
  { type: 'table', name: '数据表', icon: '📋' },
  { type: 'text', name: '文本', icon: '📝' }
]
const selectedWidgetType = ref('')
const newWidget = ref({ title: '', config: '{}' })

async function loadDashboards() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/dashboards?dashboard_type=${currentTab.value}`, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      dashboards.value = await response.json()
      if (dashboards.value.length > 0) {
        selectedDashboardId.value = dashboards.value[0].id
        await loadDashboardDetails()
      } else {
        currentDashboard.value = null
        widgets.value = []
      }
    }
  } catch (err) {
    console.error('加载仪表盘失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadDashboardDetails() {
  if (!selectedDashboardId.value) return
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/dashboards/${selectedDashboardId.value}`, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      currentDashboard.value = await response.json()
      widgets.value = currentDashboard.value.widgets || []
    }
  } catch (err) {
    console.error('加载仪表盘详情失败:', err)
  } finally {
    loading.value = false
  }
}

async function createDashboard() {
  try {
    const response = await fetch(`${API_BASE}/dashboards`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({ ...newDashboard.value, dashboard_type: currentTab.value })
    })
    if (response.ok) {
      showCreateDialog.value = false
      newDashboard.value = { name: '', type: 'personal' }
      await loadDashboards()
    }
  } catch (err) {
    console.error('创建仪表盘失败:', err)
  }
}

function selectWidgetType(type) {
  selectedWidgetType.value = type
}

function getWidgetStyle(widget) {
  const config = widget.config || {}
  return {
    gridColumn: `span ${config.colspan || 4}`,
    gridRow: `span ${config.rowspan || 3}`
  }
}

async function addWidget() {
  try {
    let config = {}
    try {
      config = JSON.parse(newWidget.value.config)
    } catch {}
    
    const response = await fetch(`${API_BASE}/dashboards/${selectedDashboardId.value}/widgets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        widget_type: selectedWidgetType.value,
        title: newWidget.value.title,
        config: config
      })
    })
    if (response.ok) {
      showWidgetDialog.value = false
      selectedWidgetType.value = ''
      newWidget.value = { title: '', config: '{}' }
      await loadDashboardDetails()
    }
  } catch (err) {
    console.error('添加组件失败:', err)
  }
}

async function deleteWidget(widget) {
  if (!confirm('确定删除此组件？')) return
  try {
    const response = await fetch(`${API_BASE}/dashboards/widgets/${widget.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      await loadDashboardDetails()
    }
  } catch (err) {
    console.error('删除组件失败:', err)
  }
}

function getWidgetComponent(type) {
  return {
    props: ['config'],
    template: '<div class="widget-placeholder">{{ config.metric || type }}</div>'
  }
}

onMounted(() => {
  loadDashboards()
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  height: 100%;
  background: var(--bg-primary);
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.tabs button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tabs button:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.tabs button.active {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  font-weight: 600;
}

.dashboard-selector {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.dashboard-select {
  padding: 10px 14px;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  font-size: 14px;
  min-width: 200px;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
  min-height: 400px;
}

.widget-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}

.widget-card:hover {
  border-color: var(--border-active);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.widget-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-icon {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 18px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: var(--bg-tertiary);
  color: var(--neon-magenta);
}

.widget-content {
  flex: 1;
}

.widget-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  font-size: 14px;
}

.widget-types {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 16px 0;
}

.widget-type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.widget-type-card:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-active);
}

.wt-icon {
  font-size: 24px;
}

.wt-name {
  font-size: 13px;
  color: var(--text-secondary);
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-panel);
  border: 1px solid var(--neon-cyan);
  border-radius: 12px;
  padding: 24px;
  width: 480px;
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
}

.dialog h2 {
  margin: 0 0 16px 0;
  color: var(--neon-cyan);
  font-size: 16px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--neon-cyan);
  box-shadow: 0 0 0 3px rgba(0, 255, 255, 0.1);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
  transform: translateY(-2px);
}

.btn-secondary {
  padding: 10px 20px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}
</style>
