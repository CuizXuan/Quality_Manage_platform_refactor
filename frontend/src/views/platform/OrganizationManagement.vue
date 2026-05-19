<template>
  <SystemCrudPage
    title="组织管理"
    kicker="Organizations"
    create-label="新建组织"
    :items="organizations"
    :fields="fields"
    @create="createOrganization"
    @update="updateOrganization"
    @remove="removeOrganization"
  />
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { systemApi } from '@/api/system'
import SystemCrudPage from './SystemCrudPage.vue'
import { formatStatus, statusOptions } from './statusOptions'

const organizations = ref([])
const fields = [
  { key: 'name', label: '组织名称', required: true },
  { key: 'code', label: '组织编码', required: true, createOnly: true },
  { key: 'description', label: '描述' },
  {
    key: 'status',
    label: '状态',
    type: 'select',
    options: statusOptions,
    formatter: formatStatus,
  },
  { key: 'sort_order', label: '排序', type: 'number' },
]

async function loadOrganizations() {
  const response = await systemApi.organizations.list()
  organizations.value = response.data
}

async function createOrganization(data) {
  await systemApi.organizations.create(data)
  await loadOrganizations()
}

async function updateOrganization(data) {
  await systemApi.organizations.update(data.id, data)
  await loadOrganizations()
}

async function removeOrganization(item) {
  await systemApi.organizations.delete(item.id)
  await loadOrganizations()
}

onMounted(loadOrganizations)
</script>
