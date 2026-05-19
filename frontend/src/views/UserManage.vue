<template>
  <div class="user-manage">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
    </div>

    <!-- 用户列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="user-table">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>角色</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="status-badge" :class="user.status">
                {{ user.status === 'active' ? '正常' : '禁用' }}
              </span>
            </td>
            <td>{{ user.roles?.join(', ') || '-' }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <button class="btn-link" @click="editUser(user)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const loading = ref(false)
const users = ref([])

async function loadUsers() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/tenant/users`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    if (response.ok) {
      users.value = await response.json()
    }
  } catch (err) {
    console.error('加载用户失败:', err)
  } finally {
    loading.value = false
  }
}

function editUser(user) {
  alert(`编辑用户: ${user.username}`)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-manage {
  padding: 24px;
  height: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary, #333);
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--text-secondary, #666);
}

.user-table table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-secondary, white);
  border-radius: 8px;
  overflow: hidden;
}

.user-table th,
.user-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-color, #eee);
  color: var(--text-primary, #333);
}

.user-table th {
  background: var(--bg-tertiary, #f5f5f5);
  font-weight: 600;
  font-size: 14px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.status-badge.active {
  background: var(--success-bg, #e6f7e6);
  color: var(--success-color, #52c41a);
}

.status-badge.disabled {
  background: var(--error-bg, #fff2f0);
  color: var(--error-color, #ff4d4f);
}

.btn-link {
  background: none;
  border: none;
  color: var(--accent-color, #667eea);
  cursor: pointer;
  font-size: 14px;
}
</style>
