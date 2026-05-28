<template>
  <div class="test-plan-detail-page">
    <!-- 标题区 -->
    <header class="page-header">
      <div class="header-left">
        <el-button text :icon="ArrowLeft" @click="goBack" />
        <div>
          <h1>{{ plan?.name || '测试计划详情' }}</h1>
          <p>{{ plan?.description }}</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="VideoPlay" :loading="running" @click="handleRunPlan">执行计划</el-button>
      </div>
    </header>

    <!-- 主体 -->
    <div class="page-body">
      <!-- 左侧套件列表 -->
      <aside class="suite-sidebar">
        <div class="sidebar-header">
          <span>测试套件</span>
          <el-button text size="small" :icon="Plus" @click="openSuiteDialog" />
        </div>
        <div class="suite-list">
          <div v-if="!plan?.suites?.length" class="empty-hint">暂无套件，点击 + 添加</div>
          <div
            v-for="suite in plan?.suites || []"
            :key="suite.id"
            class="suite-item"
            :class="{ active: selectedSuiteId === suite.id }"
            @click="selectSuite(suite)"
          >
            <span class="suite-name">{{ suite.name }}</span>
            <span class="suite-count">{{ suite.items?.length || 0 }}</span>
            <el-button text size="small" :icon="Delete" @click.stop="deleteSuite(suite.id)" />
          </div>
        </div>
      </aside>

      <!-- 右侧套件详情 -->
      <section class="suite-content">
        <div v-if="!selectedSuite" class="empty-hint-large">
          请选择一个套件查看详情
        </div>
        <template v-else>
          <!-- 套件头部 -->
          <div class="suite-header">
            <div>
              <h3>{{ selectedSuite.name }}</h3>
              <span class="suite-desc">{{ selectedSuite.description }}</span>
            </div>
            <div class="suite-actions">
              <el-button type="primary" size="small" @click="openAddItemDialog">添加用例/场景</el-button>
            </div>
          </div>

          <!-- 套件项目列表 -->
          <div class="item-list">
            <el-table :data="selectedSuite.items || []" size="small">
              <el-table-column prop="item_type" label="类型" width="80">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.item_type === 'case' ? 'primary' : 'success'">
                    {{ row.item_type === 'case' ? '用例' : '场景' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="item_name" label="名称" />
              <el-table-column prop="item_id" label="ID" width="60" />
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button type="danger" text size="small" @click="removeItem(row.id)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!selectedSuite.items?.length" class="empty-hint">暂无项目，点击"添加用例/场景"添加</div>
          </div>
        </template>
      </section>
    </div>

    <!-- 新建套件弹窗 -->
    <el-dialog v-model="showSuiteDialog" title="新建套件" width="400px" destroy-on-close>
      <el-form :model="suiteForm" label-width="80px">
        <el-form-item label="套件名称" required>
          <el-input v-model="suiteForm.name" placeholder="请输入套件名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="suiteForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSuiteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSuite">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加用例/场景弹窗 -->
    <el-dialog v-model="showAddItemDialog" title="添加用例/场景" width="600px" destroy-on-close>
      <div class="add-item-tabs">
        <el-radio-group v-model="addItemType">
          <el-radio value="case">用例</el-radio>
          <el-radio value="scenario">场景</el-radio>
        </el-radio-group>
      </div>
      <div class="add-item-list">
        <el-input v-model="searchKeyword" placeholder="搜索名称" size="small" style="margin-bottom: 10px" @input="searchItems" />
        <el-table :data="searchResults" size="small" max-height="300" @row-click="selectItem">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ row }">
              <el-button type="primary" text size="small" @click.stop="addItem(row)">添加</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ArrowLeft, Plus, Delete, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useTestPlanStore } from '@/stores/testPlanStore'
import { caseApi } from '@/api/case'
import { scenarioApi } from '@/api/scenario'

const route = useRoute()
const router = useRouter()
const store = useTestPlanStore()

const plan = ref(null)
const selectedSuiteId = ref(null)
const selectedSuite = ref(null)
const showSuiteDialog = ref(false)
const showAddItemDialog = ref(false)
const saving = ref(false)
const running = ref(false)

const suiteForm = reactive({ name: '', description: '' })
const addItemType = ref('case')
const searchKeyword = ref('')
const searchResults = ref([])

async function loadPlan() {
  const id = Number(route.params.id)
  plan.value = await store.fetchPlan(id)
  if (plan.value?.suites?.length && !selectedSuiteId.value) {
    selectSuite(plan.value.suites[0])
  }
}

function selectSuite(suite) {
  selectedSuiteId.value = suite.id
  selectedSuite.value = suite
}

async function handleSaveSuite() {
  if (!suiteForm.name) {
    ElMessage.warning('请输入套件名称')
    return
  }
  saving.value = true
  try {
    await store.createSuite(plan.value.id, { ...suiteForm })
    ElMessage.success('创建成功')
    showSuiteDialog.value = false
    suiteForm.name = ''
    suiteForm.description = ''
    loadPlan()
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    saving.value = false
  }
}

async function deleteSuite(suiteId) {
  try {
    await ElMessageBox.confirm('确认删除该套件？', '提示', { type: 'warning' })
    await store.deleteSuite(suiteId)
    ElMessage.success('删除成功')
    if (selectedSuiteId.value === suiteId) {
      selectedSuiteId.value = null
      selectedSuite.value = null
    }
    loadPlan()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleRunPlan() {
  running.value = true
  try {
    const result = await store.runPlan(plan.value.id)
    ElMessage.success(`执行已开始: ${result.id}`)
    router.push({ name: 'TestPlanRuns' })
  } catch (e) {
    ElMessage.error('执行失败')
  } finally {
    running.value = false
  }
}

async function searchItems() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    searchResults.value = []
    return
  }
  const baseParams = { keyword, page: 1, page_size: 20 }
  // Filter by plan's project/version/iteration if available
  if (plan.value?.project_id) {
    baseParams.project_id = plan.value.project_id
  }
  if (addItemType.value === 'case') {
    const res = await caseApi.list(baseParams)
    searchResults.value = res.data?.items || []
  } else {
    const res = await scenarioApi.list(baseParams)
    searchResults.value = res.data?.items || []
  }
}

function selectItem(row) {
  addItem(row)
}

async function addItem(row) {
  try {
    await store.addSuiteItem({
      suite_id: selectedSuiteId.value,
      item_type: addItemType.value,
      item_id: row.id,
    })
    ElMessage.success('添加成功')
    showAddItemDialog.value = false
    loadPlan()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeItem(itemId) {
  try {
    await store.removeSuiteItem(itemId)
    ElMessage.success('移除成功')
    loadPlan()
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

function openSuiteDialog() {
  suiteForm.name = ''
  suiteForm.description = ''
  showSuiteDialog.value = true
}

function openAddItemDialog() {
  searchKeyword.value = ''
  searchResults.value = []
  showAddItemDialog.value = true
}

function goBack() {
  router.push({ name: 'TestPlanList' })
}

onMounted(() => {
  loadPlan()
})
</script>

<style scoped>
.test-plan-detail-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
  background: var(--bg-page);
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-header);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-strong);
}

.header-left p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.page-body {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 10px;
}

.suite-sidebar {
  width: 240px;
  flex: 0 0 240px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-header);
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.suite-list {
  padding-top: 8px;
}

.suite-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
}

.suite-item:hover,
.suite-item.active {
  background: var(--el-color-primary-light-9);
}

.suite-name {
  flex: 1;
  font-size: 13px;
}

.suite-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.suite-content {
  flex: 1;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-header);
  overflow-y: auto;
}

.suite-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.suite-header h3 {
  margin: 0;
  font-size: 16px;
}

.suite-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.item-list {
  padding-top: 12px;
}

.empty-hint {
  padding: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  text-align: center;
}

.empty-hint-large {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
}

.add-item-tabs {
  margin-bottom: 12px;
}

.add-item-list {
  min-height: 200px;
}
</style>