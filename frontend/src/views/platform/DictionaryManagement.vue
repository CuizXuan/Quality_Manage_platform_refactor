<template>
  <SystemCrudPage
    title="字典管理"
    kicker="Dictionaries"
    create-label="新建字典项"
    :items="dictionaries"
    :fields="fields"
    @create="createDictionary"
    @update="updateDictionary"
    @remove="removeDictionary"
  />
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { systemApi } from '@/api/system'
import SystemCrudPage from './SystemCrudPage.vue'
import { statusOptions, formatStatus } from './statusOptions'

const dictionaries = ref([])

const fields = [
  {
    key: 'category',
    label: '分类',
    required: true,
    type: 'select',
    options: categoryOptions,
  },
  { key: 'code', label: '编码', required: true },
  { key: 'name', label: '名称', required: true },
  { key: 'sort_order', label: '排序', type: 'number' },
  {
    key: 'status',
    label: '状态',
    type: 'select',
    options: statusOptions,
    formatter: formatStatus,
  },
]

const categoryOptions = [
  { value: 'priority', label: '优先级' },
  { value: 'case_type', label: '用例类型' },
  { value: 'tag', label: '标签' },
]

async function loadDictionaries() {
  const response = await systemApi.dictionaries.list()
  dictionaries.value = response.data
}

async function createDictionary(data) {
  await systemApi.dictionaries.create(data)
  await loadDictionaries()
}

async function updateDictionary(data) {
  await systemApi.dictionaries.update(data.id, data)
  await loadDictionaries()
}

async function removeDictionary(item) {
  await systemApi.dictionaries.delete(item.id)
  await loadDictionaries()
}

onMounted(loadDictionaries)
</script>