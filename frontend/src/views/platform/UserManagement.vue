<template>
  <div class="user-management">
    <!-- 页面标题区 -->
    <div class="page-header">
      <span class="page-title">用户管理</span>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
    </div>

    <!-- 查询区 -->
    <section class="user-management__filters">
      <div class="filter-bar">
        <el-select
          v-model="draftFilters.status"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="启用" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
        <el-date-picker
          v-model="draftFilters.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          class="filter-bar__date-range"
        />
      </div>
      <div class="search-bar">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索用户名/姓名/邮箱"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
    </section>

    <!-- 数据列表 -->
    <div class="table-area">
      <el-table v-loading="loading" :data="pagedUsers" border>
        <el-table-column prop="username" label="用户名" min-width="130" show-overflow-tooltip />
        <el-table-column prop="display_name" label="姓名" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.display_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="organization_name" label="组织" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.organization_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.roles?.join('，') || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" text type="primary" @click.stop="openEdit(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click.stop="removeUser(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 — 右下角固定 -->
      <div class="pagination-area">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          prev-text="上一页"
          next-text="下一页"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 新建/编辑用户弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新建用户'" top="4vh" width="min(480px, 92vw)" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!form.id" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.display_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="密码" required>
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="组织">
          <el-select v-model="form.organization_id" placeholder="请选择组织" class="full-width">
            <el-option :value="null" label="未分配" />
            <el-option v-for="org in organizations" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-checkbox-group v-model="form.role_ids" class="check-group">
            <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">
              {{ role.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '@/api/system'

const loading = ref(false)
const saving = ref(false)
const users = ref([])
const roles = ref([])
const organizations = ref([])
const dialogVisible = ref(false)

const draftFilters = ref({
  keyword: '',
  status: '',
  date_range: null,
})

const appliedFilters = ref({
  keyword: '',
  status: '',
  date_range: null,
})
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const form = reactive(defaultForm())

const pagedUsers = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return users.value.slice(start, start + pageSize.value)
})

function defaultForm() {
  return {
    id: null,
    username: '',
    display_name: '',
    email: '',
    password: '',
    phone: '',
    organization_id: null,
    status: 'active',
    role_ids: [],
  }
}

function buildQueryParams() {
  const params = {
    page: page.value,
    page_size: pageSize.value,
  }
  if (queryForm.value.keyword) params.keyword = queryForm.value.keyword
  if (queryForm.value.status) params.status = queryForm.value.status
  return params
}

async function fetchUsers() {
  loading.value = true
  try {
    const params = buildQueryParams()
    const res = await systemApi.users.list(params)
    users.value = res.data.items || res.data || []
    total.value = res.data.total || users.value.length
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchRoles() {
  try {
    const res = await systemApi.roles.list()
    roles.value = res.data.items || res.data || []
  } catch {}
}

async function fetchOrganizations() {
  try {
    const res = await systemApi.organizations.list()
    organizations.value = res.data.items || res.data || []
  } catch {}
}

function handleSearch() {
  page.value = 1
  fetchUsers()
}

function handleReset() {
  queryForm.value.keyword = ''
  queryForm.value.status = ''
  page.value = 1
  fetchUsers()
}

function handlePageChange(p) {
  page.value = p
  fetchUsers()
}

function handleSizeChange(s) {
  pageSize.value = s
  page.value = 1
  fetchUsers()
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(user) {
  resetForm({ ...user, password: '', role_ids: [...(user.role_ids || [])] })
  dialogVisible.value = true
}

function resetForm(data = {}) {
  Object.keys(form).forEach(key => { form[key] = defaultForm()[key] })
  Object.assign(form, defaultForm(), data)
}

async function saveUser() {
  if (!form.username || !form.email) {
    ElMessage.warning('请填写用户名和邮箱')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.id) {
      delete payload.username
      delete payload.password
      await systemApi.users.update(payload.id, payload)
    } else {
      await systemApi.users.create(payload)
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeUser(user) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${user.username}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await systemApi.users.delete(user.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {}
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchOrganizations()
})
</script>

<style scoped>
.user-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-container);
  border-radius: var(--border-radius-lg);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-bar {
  background: var(--bg-container);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-md) var(--spacing-lg);
}

.filter-control {
  width: 160px;
}

.filter-keyword {
  width: 220px;
}

.filter-actions {
  margin-left: auto;
}

.table-area {
  flex: 1;
  background: var(--bg-container);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-area .el-table {
  flex: 1;
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-md) 0 0;
}

.full-width {
  width: 100%;
}

.check-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
</style>