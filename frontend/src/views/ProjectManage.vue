<template>
  <div class="project-manage">
    <div class="page-header">
      <h1 class="page-title">项目管理</h1>
      <button class="btn-primary" @click="showCreateDialog = true">
        + 新建项目
      </button>
    </div>

    <!-- 搜索筛选 -->
    <div class="filter-bar">
      <input
        v-model="searchKeyword"
        type="text"
        placeholder="搜索项目名称或Key..."
        class="search-input"
        @input="handleSearch"
      />
      <select v-model="statusFilter" class="status-filter" @change="loadProjects">
        <option value="">全部状态</option>
        <option value="active">活跃</option>
        <option value="archived">已归档</option>
      </select>
    </div>

    <!-- 项目列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="projects.length === 0" class="empty-state">
      <p>暂无项目</p>
      <button class="btn-primary" @click="showCreateDialog = true">创建第一个项目</button>
    </div>
    <div v-else class="project-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="goToProject(project)"
      >
        <div class="project-icon">
          {{ project.key.substring(0, 2) }}
        </div>
        <div class="project-info">
          <h3 class="project-name">{{ project.name }}</h3>
          <p class="project-key">{{ project.key }}</p>
          <p class="project-desc">{{ project.description || '暂无描述' }}</p>
        </div>
        <div class="project-meta">
          <span class="status-badge" :class="project.status">
            {{ project.status === 'active' ? '活跃' : '已归档' }}
          </span>
          <span class="member-count">{{ project.member_count }} 成员</span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        :disabled="page <= 1"
        @click="page--; loadProjects()"
      >
        上一页
      </button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button
        :disabled="page >= totalPages"
        @click="page++; loadProjects()"
      >
        下一页
      </button>
    </div>

    <!-- 创建项目弹窗 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog">
        <h2 class="dialog-title">新建项目</h2>
        <form @submit.prevent="handleCreate">
          <div class="form-group">
            <label>项目名称 *</label>
            <input
              v-model="createForm.name"
              type="text"
              placeholder="例如：用户服务"
              required
            />
          </div>
          <div class="form-group">
            <label>项目Key *</label>
            <input
              v-model="createForm.key"
              type="text"
              placeholder="例如：USER_SVC"
              required
              maxlength="20"
              pattern="[A-Za-z0-9_]+"
            />
            <small>只能包含字母、数字和下划线，最多20字符</small>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea
              v-model="createForm.description"
              placeholder="项目描述..."
              rows="3"
            ></textarea>
          </div>
          <div class="dialog-actions">
            <button type="button" class="btn-secondary" @click="showCreateDialog = false">
              取消
            </button>
            <button type="submit" class="btn-primary" :disabled="creating">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const API_BASE = '/api'

const loading = ref(false)
const projects = ref([])
const searchKeyword = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const totalPages = ref(1)

const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  name: '',
  key: '',
  description: ''
})

async function loadProjects() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value,
      page_size: pageSize.value
    })
    if (searchKeyword.value) params.append('keyword', searchKeyword.value)
    if (statusFilter.value) params.append('status', statusFilter.value)
    
    const response = await fetch(`${API_BASE}/projects?${params}`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      projects.value = data.items
      totalPages.value = data.total_pages
    }
  } catch (err) {
    console.error('加载项目失败:', err)
  } finally {
    loading.value = false
  }
}

let searchTimer = null
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadProjects()
  }, 300)
}

async function handleCreate() {
  creating.value = true
  try {
    const response = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify(createForm.value)
    })
    
    if (response.ok) {
      showCreateDialog.value = false
      createForm.value = { name: '', key: '', description: '' }
      loadProjects()
    } else {
      const data = await response.json()
      alert(data.detail || '创建失败')
    }
  } catch (err) {
    alert('创建失败')
  } finally {
    creating.value = false
  }
}

function goToProject(project) {
  // 跳转到项目详情页（后续可扩展为 /projects/:id）
  router.push({ name: 'Projects' })
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.project-manage {
  padding: 24px;
  height: 100%;
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
  color: var(--text-primary, #333);
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary, white);
  color: var(--text-primary, #333);
}

.status-filter {
  padding: 10px 14px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary, white);
  color: var(--text-primary, #333);
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary, #666);
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.project-card {
  background: var(--bg-secondary, white);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.project-card:hover {
  box-shadow: 0 4px 12px var(--shadow-color, rgba(0, 0, 0, 0.1));
  border-color: var(--accent-color, #667eea);
}

.project-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.project-info {
  margin-bottom: 12px;
}

.project-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.project-key {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--text-secondary, #888);
}

.project-desc {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary, #666);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: var(--success-bg, #e6f7e6);
  color: var(--success-color, #52c41a);
}

.status-badge.archived {
  background: var(--bg-tertiary, #f5f5f5);
  color: var(--text-tertiary, #999);
}

.member-count {
  font-size: 13px;
  color: var(--text-secondary, #888);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid var(--border-color, #ddd);
  background: var(--bg-secondary, white);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-primary, #333);
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-secondary, white);
  border-radius: 12px;
  padding: 24px;
  width: 480px;
  max-width: 90%;
}

.dialog-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary, #333);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  background: var(--bg-primary, white);
  color: var(--text-primary, #333);
}

.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary, #888);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: var(--bg-secondary, white);
  color: var(--text-secondary, #666);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
</style>
