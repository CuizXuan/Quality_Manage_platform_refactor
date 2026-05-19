<template>
  <SystemCrudPage
    title="菜单管理"
    kicker="Menus"
    create-label="新建菜单"
    :items="menus"
    :fields="fields"
    @create="createMenu"
    @update="updateMenu"
    @remove="removeMenu"
  />
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { systemApi } from '@/api/system'
import SystemCrudPage from './SystemCrudPage.vue'

const menus = ref([])
const fields = [
  { key: 'name', label: '菜单名称', required: true },
  { key: 'code', label: '菜单编码', required: true, createOnly: true },
  { key: 'path', label: '路径' },
  { key: 'icon', label: '图标' },
  { key: 'component', label: '组件标识' },
  { key: 'permission_code', label: '权限编码' },
  { key: 'status', label: '状态', type: 'select', options: ['active', 'disabled'] },
  { key: 'sort_order', label: '排序', type: 'number' },
]

async function loadMenus() {
  const response = await systemApi.menus.list()
  menus.value = response.data
}

async function createMenu(data) {
  await systemApi.menus.create(data)
  await loadMenus()
}

async function updateMenu(data) {
  await systemApi.menus.update(data.id, data)
  await loadMenus()
}

async function removeMenu(item) {
  await systemApi.menus.delete(item.id)
  await loadMenus()
}

onMounted(loadMenus)
</script>

