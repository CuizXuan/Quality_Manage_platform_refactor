<template>
  <SystemCrudPage
    title="角色管理"
    kicker="Roles"
    create-label="新建角色"
    :items="roles"
    :fields="fields"
    @create="createRole"
    @update="updateRole"
    @remove="removeRole"
  />
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { systemApi } from '@/api/system'
import SystemCrudPage from './SystemCrudPage.vue'

const roles = ref([])
const fields = [
  { key: 'name', label: '角色名称', required: true },
  { key: 'code', label: '角色编码', required: true, createOnly: true },
  { key: 'description', label: '描述' },
  { key: 'status', label: '状态', type: 'select', options: ['active', 'disabled'] },
  { key: 'permissionsText', label: '权限', placeholder: '例如 system:manage,user:manage' },
]

async function loadRoles() {
  const response = await systemApi.roles.list()
  roles.value = response.data.map((item) => ({
    ...item,
    permissionsText: item.permissions.join(','),
  }))
}

async function createRole(data) {
  await systemApi.roles.create({
    ...data,
    permissions: splitPermissions(data.permissionsText),
  })
  await loadRoles()
}

async function updateRole(data) {
  await systemApi.roles.update(data.id, {
    name: data.name,
    description: data.description,
    status: data.status,
    permissions: splitPermissions(data.permissionsText),
  })
  await loadRoles()
}

async function removeRole(item) {
  await systemApi.roles.delete(item.id)
  await loadRoles()
}

function splitPermissions(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

onMounted(loadRoles)
</script>

