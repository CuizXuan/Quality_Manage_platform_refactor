<template>
  <div class="case-list-container">
    <div class="list-header">
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
          <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="case_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.case_type === 'api' ? 'success' : 'warning'" size="small">
            {{ row.case_type === 'api' ? '接口' : '功能' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="getPriorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" text @click.stop="handleCopy(row)">复制</el-button>
          <el-button type="danger" size="small" text @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="caseStore.total"
      :page-sizes="[15, 30, 50, 100]"
      page-size-text="条/页"
      prev-text="上一页"
      next-text="下一页"
      layout="total, sizes, prev, pager, next"
      class="list-pagination"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCaseStore } from '@/stores/caseStore'
import { caseApi } from '@/api/case'

const emit = defineEmits(['case-selected', 'create-case'])

const props = defineProps({
  folderId: {
    type: Number,
    default: null
  }
})

const caseStore = useCaseStore()
const keyword = ref('')
const currentPage = ref(1)
const currentPageSize = ref(15)

function getPriorityType(priority) {
  const map = { P0: 'danger', P1: 'warning', P2: 'info', P3: '' }
  return map[priority] || ''
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const pad = n => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function loadCases() {
  try {
    await caseStore.fetchCases({
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

function handleCreate() {
  emit('create-case')
}

async function handleCopy(row) {
  try {
    await caseApi.copy(row.id)
    ElMessage.success('复制成功')
    loadCases()
  } catch {
    ElMessage.error('复制失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
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

watch(() => props.folderId, () => {
  currentPage.value = 1
  loadCases()
})

onMounted(() => {
  loadCases()
})

defineExpose({ reload: loadCases })
</script>

<style scoped>
.case-list-container {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.case-list-container :deep(.el-table) {
  flex: 1;
}

.case-list-container :deep(.el-table__body tr) {
  cursor: pointer;
}

.case-list-container :deep(.el-table__cell) {
  vertical-align: middle;
}

.text-ellipsis {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.list-pagination {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 16px;
}
</style>
