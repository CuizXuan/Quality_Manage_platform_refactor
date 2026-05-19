<template>
  <SystemCrudPage
    title="角色管理"
    kicker="Roles 角色"
    create-label="新建角色"
    :items="roles"
    :fields="fields"
    :actions="actions"
    @create="createRole"
    @update="updateRole"
    @remove="removeRole"
    @action="handleAction"
  />

  <el-drawer v-model="permissionDrawerVisible" :title="`配置权限：${permissionRole?.name || ''}`" size="720px" @closed="resetPermissionDrawer">
      <div class="permission-summary">
        <span>已选择 {{ permissionForm.length }} 项</span>
        <span>共 {{ permissionResources.length }} 个菜单</span>
      </div>

      <el-table :data="pagedPermissionResources" border stripe class="permission-table">
        <el-table-column prop="label" label="菜单" min-width="160" />
        <el-table-column v-for="action in permissionActions" :key="action.key" :label="action.label" align="center">
          <template #default="{ row }">
            <el-checkbox
              v-if="row.actions.includes(action.key)"
              :model-value="permissionForm.includes(`${row.key}:${action.key}`)"
              @change="togglePermission(`${row.key}:${action.key}`, $event)"
            />
              <span v-else class="muted-text">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-button :disabled="permissionPage === 1" @click="permissionPage -= 1">上一页</el-button>
        <span>第 {{ permissionPage }} / {{ permissionPageCount }} 页</span>
        <el-button
          :disabled="permissionPage === permissionPageCount"
          @click="permissionPage += 1"
        >
          下一页
        </el-button>
      </div>

      <template #footer>
      <div class="drawer-footer">
        <el-button @click="closePermissionDrawer">取消</el-button>
        <el-button type="primary" @click="savePermissions">保存权限</el-button>
      </div>
      </template>
  </el-drawer>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { systemApi } from '@/api/system'
import SystemCrudPage from './SystemCrudPage.vue'
import { permissionActions, permissionResources } from './permissionOptions'
import { formatStatus, statusOptions } from './statusOptions'

const roles = ref([])
const permissionRole = ref(null)
const permissionForm = ref([])
const permissionDrawerVisible = ref(false)
const permissionPage = ref(1)
const permissionPageSize = 8

const actions = [{ key: 'permissions', label: '授权' }]
const fields = [
  { key: 'name', label: '角色名称', required: true },
  { key: 'code', label: '角色编码', required: true, createOnly: true },
  { key: 'description', label: '描述' },
  { key: 'status', label: '状态', type: 'select', options: statusOptions, formatter: formatStatus },
  { key: 'permissions', label: '权限', formatter: formatPermissionCount, readonly: true },
]

const permissionPageCount = computed(() =>
  Math.max(1, Math.ceil(permissionResources.length / permissionPageSize)),
)

const pagedPermissionResources = computed(() => {
  const start = (permissionPage.value - 1) * permissionPageSize
  return permissionResources.slice(start, start + permissionPageSize)
})

async function loadRoles() {
  const response = await systemApi.roles.list()
  roles.value = response.data
}

async function createRole(data) {
  await systemApi.roles.create({ ...data, permissions: [] })
  await loadRoles()
}

async function updateRole(data) {
  await systemApi.roles.update(data.id, {
    name: data.name,
    description: data.description,
    status: data.status,
  })
  await loadRoles()
}

async function removeRole(item) {
  await systemApi.roles.delete(item.id)
  await loadRoles()
}

function formatPermissionCount(value = []) {
  return `已授权 ${value.length} 项`
}

function handleAction({ action, item }) {
  if (action.key !== 'permissions') return
  permissionRole.value = item
  permissionForm.value = [...item.permissions]
  permissionDrawerVisible.value = true
  permissionPage.value = 1
}

function closePermissionDrawer() {
  permissionDrawerVisible.value = false
}

function resetPermissionDrawer() {
  permissionRole.value = null
  permissionForm.value = []
  permissionPage.value = 1
}

function togglePermission(value, checked) {
  if (checked) {
    if (!permissionForm.value.includes(value)) permissionForm.value.push(value)
    return
  }
  permissionForm.value = permissionForm.value.filter((item) => item !== value)
}

async function savePermissions() {
  await systemApi.roles.update(permissionRole.value.id, {
    permissions: permissionForm.value,
  })
  closePermissionDrawer()
  await loadRoles()
}

onMounted(loadRoles)
</script>

<style scoped>
.permission-summary {
  margin-bottom: var(--spacing-md);
}

.permission-table {
  width: 100%;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
