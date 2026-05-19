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

  <div v-if="permissionRole" class="drawer-mask" @click.self="closePermissionDrawer">
    <form class="editor-drawer permission-drawer" @submit.prevent="savePermissions">
      <h3>配置权限：{{ permissionRole.name }}</h3>
      <div class="permission-summary">
        <span>已选择 {{ permissionForm.length }} 项</span>
        <span>共 {{ permissionResources.length }} 个菜单</span>
      </div>
      <table class="permission-matrix">
        <thead>
          <tr>
            <th>菜单</th>
            <th v-for="action in permissionActions" :key="action.key">{{ action.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="resource in pagedPermissionResources" :key="resource.key">
            <td>{{ resource.label }}</td>
            <td v-for="action in permissionActions" :key="action.key">
              <input
                v-if="resource.actions.includes(action.key)"
                v-model="permissionForm"
                type="checkbox"
                :value="`${resource.key}:${action.key}`"
              />
              <span v-else class="muted-text">-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="pagination-bar">
        <button type="button" :disabled="permissionPage === 1" @click="permissionPage -= 1">上一页</button>
        <span>第 {{ permissionPage }} / {{ permissionPageCount }} 页</span>
        <button
          type="button"
          :disabled="permissionPage === permissionPageCount"
          @click="permissionPage += 1"
        >
          下一页
        </button>
      </div>
      <div class="drawer-actions">
        <button type="button" @click="closePermissionDrawer">取消</button>
        <button class="primary-btn" type="submit">保存权限</button>
      </div>
    </form>
  </div>
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
  permissionPage.value = 1
}

function closePermissionDrawer() {
  permissionRole.value = null
  permissionForm.value = []
  permissionPage.value = 1
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
