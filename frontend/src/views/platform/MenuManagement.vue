<template>
  <div class="menu-management-page">
    <!-- 页面标题区 -->
    <header class="menu-management-page__header">
      <div>
        <h1>菜单管理</h1>
        <p>统一管理后台系统菜单与权限层级。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="openCreate(null)">新建菜单</el-button>
    </header>

    <!-- 查询区 -->
    <section class="menu-management-page__filters">
      <div class="filter-bar">
        <el-select
          v-model="draftFilters.status"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="启用" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
      </div>
      <div class="search-bar">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索菜单名称/编码"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
    </section>

    <!-- 数据列表 -->
    <section class="menu-management-page__table">
      <el-table
        v-loading="loading"
        :data="pagedMenus"
        row-key="id"
        height="100%"
        highlight-current-row
      >
        <el-table-column label="菜单名称" min-width="200">
          <template #default="{ row }">
            <div class="tree-cell" :style="{ paddingLeft: `${row.level * 22}px` }">
              <el-button
                v-if="row.children && row.children.length"
                text
                size="small"
                class="tree-toggle"
                @click.stop="toggleMenu(row.id)"
              >
                {{ collapsedIds.has(row.id) ? '›' : '⌄' }}
              </el-button>
              <span v-else class="tree-toggle-placeholder"></span>
              <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.path || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="图标" min-width="100" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatMenuIcon(row.icon) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="component" label="组件" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.component || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="permission_code" label="权限编码" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.permission_code || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="openCreate(row)">新增子级</el-button>
              <el-button type="primary" text size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click.stop="removeMenu(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的菜单</span>
        </template>
      </el-table>

      <div class="menu-management-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 新建/编辑菜单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑菜单' : '新建菜单'"
      top="4vh"
      width="min(520px, 92vw)"
      destroy-on-close
      append-to-body
    >
      <el-form :model="form" label-width="90px" class="menu-form">
        <el-form-item label="上级菜单">
          <el-select v-model="form.parent_id" placeholder="一级菜单" class="full-width">
            <el-option :value="null" label="一级菜单" />
            <el-option
              v-for="item in parentOptions"
              :key="item.id"
              :label="`${'　'.repeat(item.level)}${item.name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="菜单名称" required>
          <el-input v-model="form.name" placeholder="请输入菜单名称" />
        </el-form-item>
        <el-form-item label="菜单编码" required>
          <el-input v-model="form.code" :disabled="!!form.id" placeholder="请输入菜单编码" />
        </el-form-item>
        <el-form-item label="路径">
          <el-input v-model="form.path" placeholder="请输入路径" />
        </el-form-item>
        <el-form-item label="菜单图标">
          <el-radio-group v-model="form.icon" class="icon-radio-group">
            <el-radio-button v-for="option in menuIconOptions" :key="option.value" :label="option.value">
              <span class="icon-option">{{ option.symbol }}</span>
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="组件标识">
          <el-input v-model="form.component" placeholder="请输入组件路径" />
        </el-form-item>
        <el-form-item label="权限编码">
          <el-input v-model="form.permission_code" placeholder="请输入权限编码" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" class="full-width" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveMenu">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '@/api/system'
import { formatMenuIcon, menuIconOptions } from './menuIconLibrary'

const loading = ref(false)
const saving = ref(false)
const menus = ref([])
const dialogVisible = ref(false)
const collapsedIds = ref(new Set())

const draftFilters = ref({
  keyword: '',
  status: '',
})

const appliedFilters = ref({
  keyword: '',
  status: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const total = ref(0)

const form = reactive(defaultForm())

const menuTree = computed(() => buildMenuTree(menus.value))
const flatMenus = computed(() => flattenMenus(menuTree.value))
const parentOptions = computed(() => {
  const blockedIds = form.id ? getDescendantIds(form.id, menuTree.value) : new Set()
  return flatMenus.value.filter(item => item.id !== form.id && !blockedIds.has(item.id))
})
const pagedMenus = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  return flatMenus.value.slice(start, start + pagination.value.pageSize)
})

function defaultForm() {
  return {
    id: null,
    parent_id: null,
    name: '',
    code: '',
    path: '',
    icon: 'PanelLeft',
    component: '',
    permission_code: '',
    status: 'active',
    sort_order: 0,
  }
}

function buildQueryParams() {
  return {
    page: 1,
    page_size: 1000,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.status && { status: appliedFilters.value.status }),
  }
}

async function fetchMenus() {
  loading.value = true
  try {
    const res = await systemApi.menus.list(buildQueryParams())
    menus.value = res.data.items || res.data || []
    total.value = res.data.total || menus.value.length
  } catch {
    ElMessage.error('获取菜单列表失败')
  } finally {
    loading.value = false
  }
}

function buildMenuTree(items) {
  const nodes = (items || []).map(item => ({ ...item, children: [], level: 0 }))
  const nodeMap = new Map(nodes.map(item => [item.id, item]))
  const roots = []
  for (const node of nodes) {
    const parent = nodeMap.get(node.parent_id)
    if (parent) parent.children.push(node)
    else roots.push(node)
  }
  return sortMenus(roots)
}

function sortMenus(items) {
  return items
    .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
    .map(item => ({ ...item, children: sortMenus(item.children) }))
}

function flattenMenus(items, level = 0) {
  return items.flatMap(item => {
    const current = { ...item, level }
    if (collapsedIds.value.has(item.id)) return [current]
    return [current, ...flattenMenus(item.children, level + 1)]
  })
}

function getDescendantIds(id, items) {
  const found = findMenu(id, items)
  return new Set(found ? flattenAll(found.children).map(item => item.id) : [])
}

function findMenu(id, items) {
  for (const item of items) {
    if (item.id === id) return item
    const found = findMenu(id, item.children)
    if (found) return found
  }
  return null
}

function flattenAll(items) {
  return items.flatMap(item => [item, ...flattenAll(item.children)])
}

function toggleMenu(id) {
  const next = new Set(collapsedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  collapsedIds.value = next
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  fetchMenus()
}

function handleReset() {
  draftFilters.value = { keyword: '', status: '' }
  appliedFilters.value = { keyword: '', status: '' }
  pagination.value.page = 1
  fetchMenus()
}

function handlePageChange(p) {
  pagination.value.page = p
  fetchMenus()
}

function handleSizeChange(s) {
  pagination.value.pageSize = s
  pagination.value.page = 1
  fetchMenus()
}

function openCreate(parent = null) {
  resetForm({ parent_id: parent?.id || null })
  dialogVisible.value = true
}

function openEdit(item) {
  resetForm({ ...item })
  dialogVisible.value = true
}

function resetForm(data = {}) {
  Object.assign(form, defaultForm(), data)
}

async function saveMenu() {
  if (!form.name || !form.code) {
    ElMessage.warning('请填写菜单名称和编码')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.id) {
      await systemApi.menus.update(payload.id, payload)
    } else {
      delete payload.id
      await systemApi.menus.create(payload)
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    fetchMenus()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeMenu(item) {
  try {
    await ElMessageBox.confirm(`确定删除菜单「${item.name}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await systemApi.menus.delete(item.id)
    ElMessage.success('删除成功')
    fetchMenus()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(fetchMenus)
</script>

<style scoped>
/* ── 页面容器 ── */
.menu-management-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.13), transparent 30%),
    var(--bg-page);
  overflow: hidden;
}

/* ── 标题区 ── */
.menu-management-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .menu-management-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.menu-management-page__header h1,
.menu-management-page__header p {
  margin: 0;
}

.menu-management-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.menu-management-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.btn-primary-add {
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: filter 0.2s ease, transform 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ── 查询区 ── */
.menu-management-page__filters {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .menu-management-page__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
}

.filter-control {
  width: 160px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-bar__input {
  width: 320px;
}

/* ── 表格区 ── */
.menu-management-page__table {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .menu-management-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.menu-management-page__table :deep(.el-table) {
  flex: 1;
}

.menu-management-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.menu-management-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.menu-management-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.menu-management-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}

/* ── 通用 ── */
.full-width {
  width: 100%;
}

.tree-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.tree-toggle,
.tree-toggle-placeholder {
  width: 22px;
  flex: 0 0 22px;
}

.text-ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-secondary {
  color: var(--text-secondary);
  font-size: 13px;
}

.actions-cell {
  display: inline-flex;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
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

/* ── 弹窗 ── */
.icon-radio-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.icon-radio-group :deep(.el-radio-button__inner) {
  width: 100%;
  text-align: left;
}

.icon-option {
  margin-right: 4px;
}

.menu-form :deep(.el-form-item) {
  margin-bottom: 16px;
}
</style>
