<template>
  <div class="scenario-list-container">
    <div class="list-header">
      <el-input
        v-model="keyword"
        placeholder="搜索场景名称"
        style="width: 300px"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建场景</el-button>
    </div>

    <el-table
      v-loading="scenarioStore.loading"
      :data="scenarioStore.scenarios"
      style="width: 100%"
      @row-click="handleRowClick"
      highlight-current-row
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="场景名称" min-width="200">
        <template #default="{ row }">
          <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          <span class="text-ellipsis" :title="row.description">{{ row.description || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="step_count" label="步骤数" width="90" align="center" />
      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" text @click.stop="handleRun(row)">执行</el-button>
          <el-button type="primary" size="small" text @click.stop="handleCopy(row)">复制</el-button>
          <el-button type="danger" size="small" text @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="scenarioStore.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: var(--spacing-md)"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <!-- 新建场景对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建场景" width="500px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="场景名称" required>
          <el-input v-model="createForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="createForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateSubmit">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'

const router = useRouter()
const scenarioStore = useScenarioStore()

const emit = defineEmits(['scenario-selected', 'create-scenario'])

const keyword = ref('')
const currentPage = ref(1)
const currentPageSize = ref(20)
const createDialogVisible = ref(false)
const saving = ref(false)
const createForm = ref({
  name: '',
  description: '',
  status: 'active',
})

onMounted(() => {
  scenarioStore.fetchScenarios({ page: currentPage.value, page_size: currentPageSize.value })
})

function handleSearch() {
  currentPage.value = 1
  scenarioStore.fetchScenarios({
    page: currentPage.value,
    page_size: currentPageSize.value,
    keyword: keyword.value,
  })
}

function handlePageChange(page) {
  currentPage.value = page
  scenarioStore.fetchScenarios({
    page,
    page_size: currentPageSize.value,
    keyword: keyword.value,
  })
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  scenarioStore.fetchScenarios({
    page: 1,
    page_size: size,
    keyword: keyword.value,
  })
}

function handleRowClick(row) {
  router.push({ name: 'ScenarioDetail', params: { id: row.id } })
}

function handleCreate() {
  createForm.value = { name: '', description: '', status: 'active' }
  createDialogVisible.value = true
}

async function handleCreateSubmit() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入场景名称')
    return
  }
  saving.value = true
  try {
    const created = await scenarioStore.createScenario(createForm.value)
    createDialogVisible.value = false
    ElMessage.success('创建成功')
    router.push({ name: 'ScenarioDetail', params: { id: created.id } })
  } catch {
    // error handled in store
  } finally {
    saving.value = false
  }
}

async function handleRun(row) {
  try {
    await ElMessageBox.confirm(`确定要执行场景「${row.name}」吗？`, '执行确认', {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info',
    })
    const result = await scenarioStore.startExecution(row.id)
    ElMessage.success(`执行已启动 (run_id: ${result.run_id})`)
    router.push({ name: 'ExecutionDetail', params: { id: result.run_id } })
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('执行启动失败')
  }
}

async function handleCopy(row) {
  try {
    const data = await scenarioStore.createScenario({
      name: `${row.name} (副本)`,
      description: row.description,
      status: row.status,
    })
    ElMessage.success('复制成功')
    router.push({ name: 'ScenarioDetail', params: { id: data.id } })
  } catch {
    // error handled in store
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除场景「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await scenarioStore.deleteScenario(row.id)
    ElMessage.success('删除成功')
    scenarioStore.fetchScenarios({ page: currentPage.value, page_size: currentPageSize.value, keyword: keyword.value })
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.scenario-list-container {
  padding: var(--spacing-md);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}
</style>
