<template>
  <div class="api-asset-page">
    <header class="api-asset-page__header">
      <div>
        <h1>API 资产中心</h1>
        <p>统一管理接口定义资产，支持分组筛选、导入、调试、生成用例和基线生成。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="List" @click="router.push({ name: 'ImportJobs' })">导入任务</el-button>
        <el-button type="primary" :icon="Upload" @click="showImportDialog = true">导入 OpenAPI</el-button>
        <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="openCreateDialog">新建 API</el-button>
      </div>
    </header>

    <div class="api-asset-page__body">
      <aside class="api-asset-page__sidebar">
        <div class="sidebar-header">
          <span>API 分组</span>
          <el-button text size="small" :icon="Plus" @click="openGroupDialog" />
        </div>
        <div class="group-tree">
          <el-tree
            :data="groupTreeData"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            default-expand-all
            highlight-current
            :current-node-key="selectedGroupId"
            @node-click="onGroupNodeClick"
          >
            <template #default="{ data }">
              <span class="group-node">
                <span>{{ data.name }}</span>
                <el-button text size="small" :icon="Delete" @click.stop="deleteGroup(data.id)" />
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!groups.length" description="暂无分组" />
        </div>
      </aside>

      <section class="api-asset-page__content">
        <div class="api-asset-page__filters">
          <el-form :model="filters" label-position="left" class="filter-form">
            <div class="filter-form__row">
              <el-form-item label="项目" class="filter-item filter-item--project">
                <el-select v-model="filters.project_id" clearable filterable class="filter-control" placeholder="全部项目">
                  <el-option v-for="item in foundationStore.projects" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="方法" class="filter-item filter-item--method">
                <el-select v-model="filters.method" clearable class="filter-control" placeholder="全部">
                  <el-option v-for="item in methodOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="状态" class="filter-item filter-item--status">
                <el-select v-model="filters.status" clearable class="filter-control" placeholder="全部">
                  <el-option label="激活" value="active" />
                  <el-option label="归档" value="archived" />
                </el-select>
              </el-form-item>
              <el-form-item label="关键字" class="filter-item filter-item--keyword">
                <el-input
                  v-model="filters.keyword"
                  clearable
                  class="search-bar__input"
                  placeholder="搜索 API 名称或路径"
                  @keyup.enter="fetchApis"
                />
              </el-form-item>
              <div class="filter-actions">
                <el-button type="primary" :icon="Search" @click="fetchApis">查询</el-button>
                <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
              </div>
            </div>
          </el-form>
        </div>

        <div class="api-asset-page__table">
          <div class="table-toolbar">
            <div class="table-toolbar__meta">
              <strong>接口列表</strong>
              <span>共 {{ store.total }} 条，支持调试、差异比对和基线生成。</span>
            </div>
          </div>

          <el-table v-loading="store.loading" :data="store.apis" height="100%" highlight-current-row>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="API 名称" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="api-name" @click="openDetailDialog(row)">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="method" label="方法" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" min-width="220" show-overflow-tooltip />
            <el-table-column prop="summary" label="摘要" min-width="180" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '激活' : '归档' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="360" fixed="right" align="center">
              <template #default="{ row }">
                <div class="actions-cell">
                  <el-button type="primary" text size="small" @click="debugApi(row)">调试</el-button>
                  <el-button type="primary" text size="small" @click="showDiff(row)">Diff</el-button>
                  <el-button type="primary" text size="small" @click="openEditDialog(row)">编辑</el-button>
                  <el-button type="primary" text size="small" @click="openDetailDialog(row)">详情</el-button>
                  <el-button type="primary" text size="small" @click="handleGenerateCase(row)">生成用例</el-button>
                  <el-button type="primary" text size="small" @click="handleGenerateBaseline(row)">生成基线</el-button>
                  <el-button type="danger" text size="small" @click="deleteApi(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
            <template #empty>
              <span class="empty-text">暂无 API</span>
            </template>
          </el-table>

          <div class="api-asset-page__pagination">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :total="store.total"
              :page-sizes="[15, 30, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="fetchApis"
              @size-change="handleSizeChange"
            />
          </div>
        </div>
      </section>
    </div>

    <el-dialog v-model="showImportDialog" title="导入 OpenAPI" width="560px" destroy-on-close>
      <el-form :model="importForm" label-width="100px">
        <el-form-item label="导入方式">
          <el-radio-group v-model="importForm.source_type">
            <el-radio value="url">URL</el-radio>
            <el-radio value="json">JSON</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="importForm.source_type === 'url'" label="OpenAPI URL">
          <el-input v-model="importForm.source_url" placeholder="https://example.com/openapi.json" />
        </el-form-item>
        <el-form-item v-else label="JSON 内容">
          <el-input v-model="importForm.raw_content" type="textarea" :rows="8" placeholder='{"openapi":"3.0.0"}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDiffDialog" title="接口版本差异" width="640px" destroy-on-close>
      <el-descriptions v-if="diffResult" :column="1" border>
        <el-descriptions-item label="当前版本 ID">{{ diffResult.current_id }}</el-descriptions-item>
        <el-descriptions-item label="上一版本 ID">{{ diffResult.previous_id || '—' }}</el-descriptions-item>
        <el-descriptions-item label="摘要变化">{{ diffResult.changes.summary_changed ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="参数数量差">{{ diffResult.changes.parameter_delta }}</el-descriptions-item>
        <el-descriptions-item label="响应码差">{{ diffResult.changes.response_code_delta }}</el-descriptions-item>
        <el-descriptions-item label="请求体变化">{{ diffResult.changes.request_body_changed ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" :title="detailApi?.name || 'API 详情'" width="720px" destroy-on-close>
      <div v-if="detailApi" class="api-detail">
        <div class="detail-info">
          <el-tag :type="getMethodTagType(detailApi.method)" size="large">{{ detailApi.method }}</el-tag>
          <span class="detail-path">{{ detailApi.base_url }}{{ detailApi.path }}</span>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ detailApi.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ detailApi.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detailApi.status }}</el-descriptions-item>
          <el-descriptions-item label="摘要" :span="2">{{ detailApi.summary }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detailApi.description }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="debugApi(detailApi); showDetailDialog = false">调试</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateDialog" :title="editingApi ? '编辑 API' : '新建 API'" width="640px" destroy-on-close>
      <el-form :model="apiForm" label-width="100px" class="api-form">
        <el-form-item label="API 名称" required>
          <el-input v-model="apiForm.name" placeholder="请输入 API 名称" />
        </el-form-item>
        <el-form-item label="分组">
          <el-select v-model="apiForm.group_id" clearable class="filter-control" placeholder="选择分组">
            <el-option v-for="item in flatGroups" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="apiForm.project_id" clearable filterable class="filter-control" placeholder="选择项目">
            <el-option v-for="item in foundationStore.projects" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="方法" required>
          <el-select v-model="apiForm.method" class="filter-control" placeholder="选择方法">
            <el-option v-for="item in methodOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="路径" required>
          <el-input v-model="apiForm.path" placeholder="/api/v1/users" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="apiForm.base_url" placeholder="https://api.example.com" />
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="apiForm.summary" placeholder="请输入摘要" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="apiForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="apiForm.version" placeholder="1.0.0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="apiForm.status" class="filter-control">
            <el-option label="激活" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveApi">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, List, Plus, RefreshLeft, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useApiAssetStore } from '@/stores/apiAssetStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

const router = useRouter()
const store = useApiAssetStore()
const foundationStore = useQualityFoundationStore()

const methodOptions = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const filters = reactive({ keyword: '', method: '', status: '', project_id: null })
const pagination = reactive({ page: 1, pageSize: 15 })
const showImportDialog = ref(false)
const showDetailDialog = ref(false)
const showCreateDialog = ref(false)
const showDiffDialog = ref(false)
const importing = ref(false)
const saving = ref(false)
const detailApi = ref(null)
const editingApi = ref(null)
const diffResult = ref(null)

const importForm = reactive({ source_type: 'url', source_url: '', raw_content: '' })
const apiForm = reactive({
  name: '',
  method: 'GET',
  path: '',
  base_url: '',
  group_id: null,
  summary: '',
  description: '',
  version: '1.0.0',
  status: 'active',
  project_id: null,
})

const selectedGroupId = computed({
  get: () => store.selectedGroupId,
  set: (value) => store.setSelectedGroup(value),
})

const groups = computed(() => store.groups)
const flatGroups = computed(() => groups.value)
const groupTreeData = computed(() => {
  const roots = groups.value.filter((item) => !item.parent_id)
  const build = (parent) => {
    const children = groups.value.filter((item) => item.parent_id === parent.id)
    return children.length ? { ...parent, children: children.map(build) } : parent
  }
  return roots.map(build)
})

function getMethodTagType(method) {
  const map = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[method] || 'info'
}

async function fetchApis(extraParams = {}) {
  await store.fetchApis({
    page: pagination.page,
    page_size: pagination.pageSize,
    group_id: selectedGroupId.value || undefined,
    keyword: filters.keyword || undefined,
    method: filters.method || undefined,
    status: filters.status || undefined,
    project_id: filters.project_id || undefined,
    ...extraParams,
  })
}

function resetFilters() {
  filters.keyword = ''
  filters.method = ''
  filters.status = ''
  filters.project_id = null
  selectedGroupId.value = null
  fetchApis({})
}

function onGroupNodeClick(data) {
  selectedGroupId.value = data.id
  fetchApis({ group_id: data.id })
}

function handleSizeChange(size) {
  pagination.pageSize = size
  fetchApis()
}

async function handleImport() {
  if (importForm.source_type === 'url' && !importForm.source_url.trim()) {
    ElMessage.warning('请输入 OpenAPI URL')
    return
  }
  importing.value = true
  try {
    const result = await store.importOpenapi({
      source_type: importForm.source_type,
      source_url: importForm.source_url || undefined,
      raw_content: importForm.raw_content || undefined,
      project_id: filters.project_id || undefined,
    })
    ElMessage.success(result.message || `导入成功: ${result.imported} 个 API`)
    showImportDialog.value = false
    importForm.source_url = ''
    importForm.raw_content = ''
    await store.fetchGroups({ project_id: filters.project_id || undefined })
    await fetchApis()
  } catch (error) {
    ElMessage.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

function openDetailDialog(api) {
  detailApi.value = api
  showDetailDialog.value = true
}

function openCreateDialog() {
  editingApi.value = null
  Object.assign(apiForm, {
    name: '',
    method: 'GET',
    path: '',
    base_url: '',
    group_id: null,
    summary: '',
    description: '',
    version: '1.0.0',
    status: 'active',
    project_id: filters.project_id,
  })
  showCreateDialog.value = true
}

function openEditDialog(api) {
  editingApi.value = api
  Object.assign(apiForm, {
    name: api.name,
    method: api.method,
    path: api.path,
    base_url: api.base_url || '',
    group_id: api.group_id,
    summary: api.summary || '',
    description: api.description || '',
    version: api.version || '1.0.0',
    status: api.status || 'active',
    project_id: api.project_id,
  })
  showCreateDialog.value = true
}

function openGroupDialog() {
  ElMessageBox.prompt('请输入分组名称', '新建分组')
    .then(({ value }) => {
      if (!value?.trim()) return
      return store.createGroup({ name: value.trim(), project_id: filters.project_id || undefined }).then(() => {
        return store.fetchGroups({ project_id: filters.project_id || undefined })
      })
    })
    .catch(() => {})
}

function deleteGroup(id) {
  ElMessageBox.confirm('确认删除该分组？', '提示', { type: 'warning' })
    .then(async () => {
      await store.deleteGroup(id)
      if (selectedGroupId.value === id) selectedGroupId.value = null
      await store.fetchGroups({ project_id: filters.project_id || undefined })
    })
    .catch(() => {})
}

async function handleSaveApi() {
  if (!apiForm.name || !apiForm.method || !apiForm.path) {
    ElMessage.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    if (editingApi.value) {
      await store.updateApi(editingApi.value.id, { ...apiForm })
      ElMessage.success('更新成功')
    } else {
      await store.createApi({ ...apiForm })
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    await fetchApis()
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function debugApi(api) {
  try {
    const payload = await store.getDebugPayload(api.id)
    router.push({
      name: 'Terminal',
      query: {
        method: payload.method,
        url: payload.url,
        headers: JSON.stringify(payload.headers || {}),
        query_params: JSON.stringify(payload.query_params || {}),
        body_type: payload.body_type || 'none',
        body: payload.body || '',
      },
    })
  } catch {
    router.push({ name: 'Terminal' })
  }
}

async function showDiff(api) {
  try {
    diffResult.value = await store.getDiff(api.id)
    showDiffDialog.value = true
  } catch (error) {
    ElMessage.error(error.message || '获取差异失败')
  }
}

async function handleGenerateCase(api) {
  try {
    const result = await store.generateCase(api.id)
    ElMessage.success(`用例生成成功: ${result.name}`)
  } catch (error) {
    ElMessage.error(error.message || '生成用例失败')
  }
}

async function handleGenerateBaseline(api) {
  try {
    const result = await store.generateBaseline(api.id)
    ElMessage.success(`已生成基线: ${result.test_case.name}`)
  } catch (error) {
    ElMessage.error(error.message || '生成基线失败')
  }
}

async function deleteApi(api) {
  try {
    await ElMessageBox.confirm(`确定要删除 API「${api.name}」吗？`, '删除确认', { type: 'warning' })
    await store.deleteApi(api.id)
    ElMessage.success('删除成功')
    await fetchApis()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  await foundationStore.fetchProjects()
  await store.fetchGroups({ project_id: filters.project_id || undefined })
  await fetchApis()
})
</script>

<style scoped>
.api-asset-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
  overflow: hidden;
}

.api-asset-page__header,
.api-asset-page__filters,
.api-asset-page__sidebar,
.api-asset-page__table {
  position: relative;
  z-index: 1;
}

.api-asset-page__body {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.api-asset-page__sidebar {
  display: flex;
  flex-direction: column;
  width: 220px;
  flex: 0 0 220px;
  padding: 12px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  border-bottom: 1px solid rgba(56, 189, 248, 0.1);
}

.group-tree {
  flex: 1;
  overflow: auto;
  padding-top: 8px;
}

.group-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.api-asset-page__content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 10px;
}

.api-asset-page__filters {
  padding: 12px 16px;
}

.filter-item {
  display: flex;
  align-items: flex-end;
}

.filter-form__row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-item--project {
  width: 220px;
}

.filter-item--method,
.filter-item--status {
  width: 180px;
}

.filter-item--keyword {
  width: 300px;
}

.filter-control {
  width: 100%;
}

.search-bar__input {
  width: 300px;
}

.api-asset-page__table {
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
}

.table-toolbar__meta {
  display: grid;
  gap: 4px;
}

.table-toolbar__meta strong {
  color: var(--text-strong);
  font-size: 15px;
}

.table-toolbar__meta span {
  color: var(--text-secondary);
  font-size: 12px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-left: auto;
}

.api-asset-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 10px;
}

.api-name {
  cursor: pointer;
  color: #38bdf8;
  font-weight: 600;
}

.api-name:hover {
  text-decoration: underline;
}

.actions-cell {
  display: inline-flex;
  justify-content: center;
  gap: 4px;
  flex-wrap: wrap;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

.api-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-path {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-primary);
}

.api-form .filter-control {
  width: 180px;
}
</style>
