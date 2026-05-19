<template>
  <div class="case-list-container">
    <div class="header">
      <el-input
        v-model="keyword"
        placeholder="搜索用例名称"
        style="width: 300px"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建用例</el-button>
    </div>

    <el-table
      v-loading="caseStore.loading"
      :data="caseStore.cases"
      style="width: 100%"
      @row-click="handleRowClick"
      highlight-current-row
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="用例名称" min-width="200">
        <template #default="{ row }">
          <span class="case-name" :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="method" label="方法" width="100">
        <template #default="{ row }">
          <el-tag :type="getMethodType(row.method)" size="small">{{ row.method }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="url" label="URL" min-width="300">
        <template #default="{ row }">
          <span class="case-url" :title="row.url">{{ row.url }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="150">
        <template #default="{ row }">
          <span class="case-desc" :title="row.description">{{ row.description || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" size="small" text @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="caseStore.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 16px"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { useCaseStore } from '@/stores/caseStore'

const emit = defineEmits(['case-selected', 'create-case'])

const props = defineProps({
  caseType: {
    type: String,
    default: 'api'
  },
  folderId: {
    type: Number,
    default: null
  }
})

const caseStore = useCaseStore()

const keyword = ref('')
const currentPage = ref(1)
const currentPageSize = ref(20)

const methodTypes = {
  GET: '',
  POST: 'success',
  PUT: 'warning',
  DELETE: 'danger',
  PATCH: 'info',
}

function getMethodType(method) {
  return methodTypes[method?.toUpperCase()] || ''
}

watch(() => props.caseType, () => {
  currentPage.value = 1
  loadCases()
})

watch(() => props.folderId, () => {
  currentPage.value = 1
  loadCases()
})

async function loadCases() {
  try {
    await caseStore.fetchCases({
      case_type: props.caseType,
      folder_id: props.folderId || undefined,
      page: currentPage.value,
      page_size: currentPageSize.value,
      keyword: keyword.value || undefined,
    })
  } catch {
    ElMessage.error(caseStore.error || '加载用例失败')
  }
}

function handleSearch() {
  currentPage.value = 1
  loadCases()
}

function handlePageChange(page) {
  currentPage.value = page
  loadCases()
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  loadCases()
}

function handleRowClick(row) {
  emit('case-selected', row)
}

async function handleCreate() {
  emit('create-case')
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例 "${row.name}" 吗？`, '确认删除', {
      type: 'warning',
    })
    await caseStore.deleteCase(row.id)
    ElMessage.success('删除成功')
    if (caseStore.cases.length === 0 && currentPage.value > 1) {
      currentPage.value--
      loadCases()
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(caseStore.error || '删除失败')
    }
  }
}

onMounted(() => {
  loadCases()
})

defineExpose({
  reload: loadCases,
})
</script>

<style scoped>
.case-list-container {
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.case-name,
.case-url,
.case-desc {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}
</style>
