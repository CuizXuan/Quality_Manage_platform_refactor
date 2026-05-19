<template>
  <div class="team-manage">
    <div class="page-header">
      <h1 class="page-title">团队管理</h1>
    </div>

    <!-- 角色列表 -->
    <div class="section">
      <h2 class="section-title">角色权限</h2>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else class="role-list">
        <div v-for="role in roles" :key="role.id" class="role-card">
          <div class="role-header">
            <h3>{{ role.name }}</h3>
            <span v-if="role.is_system" class="system-badge">系统内置</span>
          </div>
          <p class="role-desc">{{ role.description || '暂无描述' }}</p>
          <div class="role-meta">
            <span>{{ role.is_system ? '系统角色' : '自定义角色' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const loading = ref(false)
const roles = ref([])

async function loadRoles() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/tenant/roles`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    if (response.ok) {
      roles.value = await response.json()
    }
  } catch (err) {
    console.error('加载角色失败:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.team-manage {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.role-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.role-card {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 16px;
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.role-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.system-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: #f5f5f5;
  color: #888;
  border-radius: 10px;
}

.role-desc {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.role-meta {
  font-size: 12px;
  color: #999;
}
</style>
