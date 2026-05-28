<template>
  <div class="api-asset-page">
    <!-- 标题区 -->
    <header class="api-asset-page__header">
      <div>
        <h1>API 资产中心</h1>
        <p>统一管理接口定义资产，支持 OpenAPI 导入与接口版本追踪。</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Upload" @click="showImportDialog = true">导入 OpenAPI</el-button>
        <el-button type="primary" :icon="Plus" class="btn-primary-add" @click="openCreateDialog">新建 API</el-button>
      </div>
    </header>

    <!-- 主体：左侧分组树 + 右侧 API 列表 -->
    <div class="api-asset-page__body">
      <!-- 左侧分组树 -->
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
            <template #default="{ node, data }">
              <span class="group-node">
                <span>{{ data.name }}</span>
                <el-button text size="small" :icon="Delete" @click.stop="deleteGroup(data.id)" />
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!groups.length" description="暂无分组" />
        </div>
      </aside>

      <!-- 右侧 API 列表 -->
      <section class="api-asset-page__content">
        <!-- 查询栏 -->
        <div class="api-asset-page__filters">
          <el-form :inline="false" :model="filters" label-position="left" class="filter-form">
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12" :md="8">
                <el-form-item label="关键词：" class="filter-item">
                  <el-input v-model="filters.keyword" placeholder="搜索 API 名称或路径" clearable class="search-bar__input" @keyup.enter="fetchApis" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="5">
                <el-form-item label="方法：" class="filter-item">
                  <el-select v-model="filters.method" placeholder="全部" clearable class="filter-control">
                    <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="5">
                <el-form-item label="状态：" class="filter-item">
                  <el-select v-model="filters.status" placeholder="全部" clearable class="filter-control">
                    <el-option label="激活" value="active" />
                    <el-option label="归档" value="archived" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="5">
                <el-form-item label="项目：" class="filter-item">
                  <el-select v-model="filters.project_id" placeholder="全部项目" clearable filterable class="filter-control" @change="onProjectFilterChange">
                    <el-option v-for="p in foundationStore.projects" :key="p.id" :label="p.name" :value="p.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <div class="filter-actions">
                  <el-button type="primary" :icon="Search" @click="fetchApis">查询</el-button>
                  <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
                </div>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- 数据列表 -->
        <div class="api-asset-page__table">
          <el-table v-loading="store.loading" :data="store.apis" height="100%" highlight-current-row>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="API 名称" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="api-name" @click="openDetailDialog(row)">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="method" label="方法" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getMethodTagType(row.method)" size="small">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
            <el-table-column prop="summary" label="简介" min-width="160" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '激活' : '归档' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right" align="center">
              <template #default="{ row }">
                <div class="actions-cell">
                  <el-button type="primary" text size="small" @click="debugApi(row)">调试</el-button>
                  <el-button type="primary" text size="small" @click="openEditDialog(row)">编辑</el-button>
                  <el-button type="primary" text size="small" @click="openDetailDialog(row)">详情</el-button>
                  <el-button type="primary" text size="small" @click="handleGenerateCase(row)">生成用例</el-button>
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
              prev-text="上一页"
              next-text="下一页"
              @current-change="fetchApis"
              @size-change="handleSizeChange"
            />
          </div>
        </div>
      </section>
    </div>

    <!-- OpenAPI 导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="导入 OpenAPI" width="500px" destroy-on-close>
      <el-form :model="importForm" label-width="100px">
        <el-form-item label="导入方式">
          <el-radio-group v-model="importForm.source_type">
            <el-radio value="url">URL 导入</el-radio>
            <el-radio value="json">JSON 内容</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="importForm.source_type === 'url'" label="OpenAPI URL">
          <el-input v-model="importForm.source_url" placeholder="https://petstore.swagger.io/v2/swagger.json" />
        </el-form-item>
        <el-form-item v-else label="JSON 内容">
          <el-input v-model="importForm.raw_content" type="textarea" :rows="8" placeholder='{"openapi":"3.0.0", ...}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- API 详情弹窗 -->
    <el-dialog v-model="showDetailDialog" :title="detailApi?.name || 'API 详情'" width="700px" destroy-on-close>
      <div v-if="detailApi" class="api-detail">
        <div class="detail-info">
          <el-tag :type="getMethodTagType(detailApi.method)" size="large">{{ detailApi.method }}</el-tag>
          <span class="detail-path">{{ detailApi.base_url }}{{ detailApi.path }}</span>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ detailApi.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ detailApi.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detailApi.status }}</el-descriptions-item>
          <el-descriptions-item label="简介" :span="2">{{ detailApi.summary }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detailApi.description }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="detailApi.parameters?.length" class="detail-section">
          <h4>参数</h4>
          <el-table :data="detailApi.parameters" size="small">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column prop="in" label="位置" width="80" />
            <el-table-column prop="required" label="必填" width="60">
              <template #default="{ row }">{{ row.required ? '是' : '否' }}</template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>
        <div v-if="detailApi.responses && Object.keys(detailApi.responses).length" class="detail-section">
          <h4>响应</h4>
          <div v-for="(val, key) in detailApi.responses" :key="key" class="response-item">
            <el-tag size="small">{{ key }}</el-tag>
            <span>{{ val.description || '' }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="debugApi(detailApi); showDetailDialog = false">调试</el-button>
      </template>
    </el-dialog>

    <!-- 新建 API 弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="editingApi ? '编辑 API' : '新建 API'" width="600px" destroy-on-close>
      <el-form :model="apiForm" label-width="100px" class="api-form">
        <el-form-item label="API 名称" required>
          <el-input v-model="apiForm.name" placeholder="请输入 API 名称" />
        </el-form-item>
        <el-form-item label="分组">
          <el-select v-model="apiForm.group_id" placeholder="选择分组" clearable class="filter-control">
            <el-option v-for="g in flatGroups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="apiForm.project_id" placeholder="选择项目" clearable filterable class="filter-control">
            <el-option v-for="p in foundationStore.projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="方法" required>
          <el-select v-model="apiForm.method" placeholder="请选择方法" class="filter-control">
            <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="路径" required>
          <el-input v-model="apiForm.path" placeholder="/api/v1/users" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="apiForm.base_url" placeholder="https://api.example.com" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="apiForm.summary" placeholder="请输入简介" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Search, RefreshLeft, Upload, Delete } from '@element-plus/icons-vue'
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
const importing = ref(false)
const saving = ref(false)
const detailApi = ref(null)
const editingApi = ref(null)

const importForm = reactive({ source_type: 'url', source_url: '', raw_content: '' })

const apiForm = reactive({
  name: '', method: 'GET', path: '', base_url: '', group_id: null,
  summary: '', description: '', version: '1.0.0', status: 'active',
  project_id: null,
})

const selectedGroupId = computed({
  get: () => store.selectedGroupId,
  set: (val) => store.setSelectedGroup(val),
})

const groups = computed(() => store.groups)
const groupTreeData = computed(() => {
  const roots = groups.value.filter(g => !g.parent_id)
  const build = (parent) => {
    const children = groups.value.filter(g => g.parent_id === parent.id)
    return children.length ? { ...parent, children: children.map(build) } : parent
  }
  return roots.map(build)
})
const flatGroups = computed(() => groups.value)

function getMethodTagType(method) {
  const map = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return map[method] || 'info'
}

function onGroupNodeClick(data) {
  selectedGroupId.value = data.id
  filters.keyword = ''
  filters.method = ''
  filters.status = ''
  fetchApis({ group_id: data.id })
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

function onProjectFilterChange() {
  pagination.page = 1
  fetchApis()
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
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
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
  Object.assign(apiForm, { name: '', method: 'GET', path: '', base_url: '', group_id: null, summary: '', description: '', version: '1.0.0', status: 'active', project_id: filters.project_id })
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
  ElMessageBox.prompt('请输入分组名称', '新建分组').then(({ value }) => {
    if (!value?.trim()) return
    store.createGroup({ name: value.trim(), project_id: filters.project_id || undefined }).then(() => store.fetchGroups({ project_id: filters.project_id || undefined }))
  }).catch(() => {})
}

function deleteGroup(id) {
  ElMessageBox.confirm('确认删除该分组？', '提示', { type: 'warning' }).then(async () => {
    await store.deleteGroup(id)
    if (selectedGroupId.value === id) selectedGroupId.value = null
    store.fetchGroups()
  }).catch(() => {})
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
    fetchApis()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function debugApi(api) {
  try {
    const payload = await store.getDebugPayload(api.id)
    // Navigate to terminal with pre-filled data via query params
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
    // Open terminal at least
    router.push({ name: 'Terminal' })
  }
}

async function handleGenerateCase(api) {
  try {
    const result = await store.generateCase(api.id)
    ElMessage.success(`用例生成成功: ${result.name}`)
  } catch (e) {
    ElMessage.error(e.message || '生成用例失败')
  }
}

async function deleteApi(api) {
  try {
    await ElMessageBox.confirm(`确定要删除 API「${api.name}」吗？`, '删除确认', { type: 'warning' })
    await store.deleteApi(api.id)
    ElMessage.success('删除成功')
    fetchApis()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  foundationStore.fetchProjects()
  await store.fetchGroups({ project_id: filters.project_id || undefined })
  fetchApis()
})
</script>

<style scoped>
@keyframes api-asset-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

.api-asset-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
}

.api-asset-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: api-asset-scan 14s linear infinite;
  z-index: 0;
}

/* Header */
.api-asset-page__header {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42));
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
}

.api-asset-page__header h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.api-asset-page__header p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-primary-add {
  position: relative;
  z-index: 1;
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* Body */
.api-asset-page__body {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 10px;
}

/* Sidebar */
.api-asset-page__sidebar {
  display: flex;
  flex-direction: column;
  width: 220px;
  flex: 0 0 220px;
  padding: 12px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(12px);
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

/* Content */
.api-asset-page__content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 10px;
}

/* Filters */
.api-asset-page__filters {
  position: relative;
  z-index: 1;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(12px);
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
}

.filter-form :deep(.el-row) {
  align-items: flex-end;
  row-gap: 8px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.filter-item {
  display: flex;
  align-items: flex-end;
  margin-bottom: 0;
  width: 100%;
}

.filter-control {
  width: 100%;
}

.search-bar__input :deep(.el-input) {
  width: 280px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  margin-left: auto;
}

.filter-actions :deep(.el-button),
.filter-actions .el-button {
  min-width: 76px;
  height: 34px;
  margin-left: 0;
}

/* Table */
.api-asset-page__table {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(12px);
}

.api-asset-page__table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(56, 189, 248, 0.08);
}

.api-asset-page__table :deep(.el-table__header th) {
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 13px;
}

.api-asset-page__table :deep(.el-table__body td) {
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.api-asset-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

.api-asset-page__table :deep(.el-table__row:hover > td) {
  background: var(--color-primary-soft) !important;
  background-color: var(--color-primary-soft) !important;
}

.api-asset-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 0 0;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
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
}

.actions-cell :deep(.el-button) {
  margin-left: 0;
  padding: 0 3px;
  font-size: 12px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

/* API Detail */
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

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-section h4 {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.response-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.api-form .filter-control {
  width: 180px;
}

/* ── 浅色主题 ── */
html:not(.dark) .api-asset-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .api-asset-page__filters,
html:not(.dark) .api-asset-page__sidebar,
html:not(.dark) .api-asset-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .api-asset-page__sidebar {
  background-size: 26px 26px, 26px 26px, auto, auto;
}

html:not(.dark) .api-asset-page__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .api-asset-page__table :deep(.el-table__body td) {
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

html:not(.dark) .api-asset-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .api-asset-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

@media (prefers-reduced-motion: reduce) {
  .api-asset-page::before {
    animation: none;
  }
}
</style>