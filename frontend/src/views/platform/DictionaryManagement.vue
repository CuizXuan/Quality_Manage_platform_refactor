<template>
  <div class="dictionary-page">
    <div class="page-header">
      <span class="page-title">字典管理</span>
    </div>

    <div class="dict-layout">
      <!-- 左侧：字典类型列表 -->
      <div class="panel">
        <div class="panel-head">
          <span class="section-label">字典类型</span>
          <el-button type="primary" @click="openTypeDialog()">+ 新建类型</el-button>
        </div>

        <div class="toolbar">
          <el-input
            v-model="typeKeyword"
            placeholder="搜索编码或名称"
            prefix-icon="Search"
            clearable
            style="width: 200px"
            @input="onTypeSearch"
          />
        </div>

        <el-table
          ref="typeTableRef"
          :data="typeList"
          border
          highlight-current-row
          v-loading="typeLoading"
          class="data-table"
          @row-click="onTypeRowClick"
        >
          <el-table-column prop="code" label="编码" min-width="100" show-overflow-tooltip />
          <el-table-column prop="name" label="名称" min-width="100" show-overflow-tooltip />
          <el-table-column prop="sort_order" label="排序" width="80" align="center" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center">
            <template #default="{ row }">
              <div class="row-actions">
                <el-button size="small" text type="primary" @click.stop="openTypeDialog(row)">编辑</el-button>
                <el-button size="small" text type="danger" @click.stop="deleteType(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="typePage"
            v-model:page-size="typePageSize"
            :total="typeTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            background
          />
        </div>
      </div>

      <!-- 右侧：字典项管理 -->
      <div class="panel">
        <template v-if="!selectedType">
          <div class="empty-state">
            <el-icon :size="48"><Document /></el-icon>
            <p>请从左侧选择字典类型</p>
          </div>
        </template>

        <template v-else>
          <div class="panel-head">
            <div class="right-title">
              <span class="section-label">字典项管理</span>
              <span class="title-divider">—</span>
              <el-tag size="small" type="primary">{{ selectedType.code }}</el-tag>
              <span class="title-name">({{ selectedType.name }})</span>
            </div>
            <el-button type="primary" @click="openItemDialog()">+ 新建字典项</el-button>
          </div>

          <div class="toolbar">
            <el-input
              v-model="itemKeyword"
              placeholder="搜索编码或名称"
              prefix-icon="Search"
              clearable
              style="width: 200px"
              @input="onItemSearch"
            />
          </div>

          <el-table
            :data="itemList"
            border
            v-loading="itemLoading"
            class="data-table"
            row-key="id"
          >
            <el-table-column prop="code" label="编码" min-width="100" show-overflow-tooltip />
            <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="value" label="存储值" min-width="120" show-overflow-tooltip />
            <el-table-column prop="sort_order" label="排序" width="80" align="center" />
            <el-table-column label="默认" width="80" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="warning" size="small">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" align="center" fixed="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <el-button size="small" text type="primary" @click="openItemDialog(row)">编辑</el-button>
                  <el-button size="small" text type="warning" @click="toggleItemStatus(row)">
                    {{ row.status === 'active' ? '禁用' : '启用' }}
                  </el-button>
                  <el-button size="small" text type="danger" @click="deleteItem(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-bar">
            <el-pagination
              v-model:current-page="itemPage"
              v-model:page-size="itemPageSize"
              :total="itemTotal"
              :page-sizes="[15, 30, 50]"
              layout="total, sizes, prev, pager, next"
              background
            />
          </div>
        </template>
      </div>
    </div>

    <!-- 字典类型 Dialog -->
    <el-dialog v-model="typeDialogVisible" :title="typeForm.id ? '编辑类型' : '新建类型'" width="480px">
      <el-form :model="typeForm" label-position="top" class="dict-form">
        <el-form-item label="编码" required>
          <el-input v-model="typeForm.code" :disabled="!!typeForm.id" placeholder="唯一编码，如 priority" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="typeForm.name" placeholder="类型名称，如 优先级" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="typeForm.description" placeholder="类型描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="typeForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="typeForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="typeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitType">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 字典项 Dialog -->
    <el-dialog v-model="itemDialogVisible" :title="itemForm.id ? '编辑字典项' : '新建字典项'" width="480px">
      <el-form :model="itemForm" label-position="top" class="dict-form">
        <el-form-item label="所属类型" required>
          <el-select v-model="itemForm.type_id" :disabled="!!itemForm.id" placeholder="选择字典类型" class="full-width">
            <el-option v-for="t in typeList" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="编码" required>
          <el-input v-model="itemForm.code" :disabled="!!itemForm.id" placeholder="唯一编码，如 P0" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="itemForm.name" placeholder="显示名称，如 P0-紧急" />
        </el-form-item>
        <el-form-item label="存储值">
          <el-input v-model="itemForm.value" placeholder="存储值，默认同编码" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="itemForm.color" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="itemForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="itemForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="默认">
          <el-switch v-model="itemForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button @click="itemDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitItem">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import { dictTypeApi, dictItemApi } from '@/api/dictionary'

// ===== 类型管理 =====
const typeTableRef = ref(null)
const typeList = ref([])
const typeLoading = ref(false)
const typePage = ref(1)
const typePageSize = ref(10)
const typeTotal = ref(0)
const typeKeyword = ref('')
const selectedType = ref(null)

const typeDialogVisible = ref(false)
const typeForm = reactive({
  id: null,
  code: '',
  name: '',
  description: '',
  sort_order: 0,
  status: 'active',
})

async function loadTypes() {
  typeLoading.value = true
  try {
    const params = { page: typePage.value, page_size: typePageSize.value }
    if (typeKeyword.value) params.keyword = typeKeyword.value
    const res = await dictTypeApi.list(params)
    typeList.value = res.data.items
    typeTotal.value = res.data.total
  } catch {
    ElMessage.error('加载字典类型失败')
  } finally {
    typeLoading.value = false
  }
}

let typeSearchTimer = null
function onTypeSearch() {
  clearTimeout(typeSearchTimer)
  typeSearchTimer = setTimeout(() => {
    typePage.value = 1
    loadTypes()
  }, 300)
}

function onTypeRowClick(row) {
  selectedType.value = row
  itemPage.value = 1
  itemKeyword.value = ''
  loadItems()
}

function openTypeDialog(row = null) {
  if (row) {
    Object.assign(typeForm, {
      id: row.id,
      code: row.code,
      name: row.name,
      description: row.description || '',
      sort_order: row.sort_order,
      status: row.status,
    })
  } else {
    Object.assign(typeForm, { id: null, code: '', name: '', description: '', sort_order: 0, status: 'active' })
  }
  typeDialogVisible.value = true
}

async function submitType() {
  try {
    if (typeForm.id) {
      await dictTypeApi.update(typeForm.id, typeForm)
      ElMessage.success('更新成功')
    } else {
      await dictTypeApi.create(typeForm)
      ElMessage.success('创建成功')
    }
    typeDialogVisible.value = false
    await loadTypes()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function deleteType(row) {
  try {
    await ElMessageBox.confirm(`确定删除类型「${row.name}」？将同时删除该类型下所有字典项。`, '删除确认', {
      type: 'warning',
    })
    await dictTypeApi.delete(row.id)
    ElMessage.success('删除成功')
    if (selectedType.value?.id === row.id) {
      selectedType.value = null
      itemList.value = []
      itemTotal.value = 0
    }
    await loadTypes()
  } catch {
    // 用户取消
  }
}

// ===== 字典项管理 =====
const itemKeyword = ref('')
const itemList = ref([])
const itemLoading = ref(false)
const itemPage = ref(1)
const itemPageSize = ref(15)
const itemTotal = ref(0)

const itemDialogVisible = ref(false)
const itemForm = reactive({
  id: null,
  type_id: null,
  code: '',
  name: '',
  value: '',
  color: '',
  sort_order: 0,
  status: 'active',
  is_default: false,
})

async function loadItems() {
  if (!selectedType.value) return
  itemLoading.value = true
  try {
    const params = {
      type_id: selectedType.value.id,
      page: itemPage.value,
      page_size: itemPageSize.value,
    }
    if (itemKeyword.value) params.keyword = itemKeyword.value
    const res = await dictItemApi.list(params)
    itemList.value = res.data.items
    itemTotal.value = res.data.total
  } catch {
    ElMessage.error('加载字典项失败')
  } finally {
    itemLoading.value = false
  }
}

let itemSearchTimer = null
function onItemSearch() {
  clearTimeout(itemSearchTimer)
  itemSearchTimer = setTimeout(() => {
    itemPage.value = 1
    loadItems()
  }, 300)
}

function openItemDialog(row = null) {
  if (row) {
    Object.assign(itemForm, {
      id: row.id,
      type_id: row.type_id,
      code: row.code,
      name: row.name,
      value: row.value || '',
      color: row.color || '',
      sort_order: row.sort_order,
      status: row.status,
      is_default: !!row.is_default,
    })
  } else {
    Object.assign(itemForm, {
      id: null,
      type_id: selectedType.value.id,
      code: '',
      name: '',
      value: '',
      color: '',
      sort_order: 0,
      status: 'active',
      is_default: false,
    })
  }
  itemDialogVisible.value = true
}

async function submitItem() {
  try {
    if (itemForm.id) {
      await dictItemApi.update(itemForm.id, itemForm)
      ElMessage.success('更新成功')
    } else {
      await dictItemApi.create(itemForm)
      ElMessage.success('创建成功')
    }
    itemDialogVisible.value = false
    await loadItems()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function toggleItemStatus(row) {
  try {
    await dictItemApi.toggleStatus(row.id)
    ElMessage.success(row.status === 'active' ? '已禁用' : '已启用')
    await loadItems()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function deleteItem(row) {
  try {
    await ElMessageBox.confirm(`确定删除字典项「${row.name}」？`, '删除确认', { type: 'warning' })
    await dictItemApi.delete(row.id)
    ElMessage.success('删除成功')
    await loadItems()
  } catch {
    // 用户取消
  }
}

watch(typePage, loadTypes)
watch(typePageSize, () => { typePage.value = 1; loadTypes() })
watch(itemPage, loadItems)
watch(itemPageSize, () => { itemPage.value = 1; loadItems() })

onMounted(() => {
  loadTypes()
})
</script>

<style scoped>
.dictionary-page {
  height: 100%;
  background-color: var(--bg-page);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-header {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.dict-layout {
  display: flex;
  gap: var(--spacing-md);
  flex: 1;
  min-height: 0;
  height: calc(100vh - 140px);
}

/* ===== 统一面板（复用 global.css .panel） ===== */
.panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* panel-head 复用 global.css .panel-head 样式（min-height: 64px, padding, border-bottom） */

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  min-height: 64px;
  padding: 0 var(--spacing-lg);
  border-bottom: 1px solid var(--border-color-lighter);
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ===== 工具栏 ===== */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-lg);
}

/* ===== data-table 复用 global.css ===== */
.data-table {
  width: 100%;
  flex: 1;
  overflow: auto;
}

/* 行操作按钮不换行 */
.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: nowrap;
}

/* ===== 右侧标题 ===== */
.right-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.title-divider {
  color: var(--text-secondary);
  margin: 0 2px;
}

.title-name {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 400;
}

/* ===== 分页栏 ===== */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-lg);
}

/* ===== 空状态 ===== */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  color: var(--text-secondary);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* ===== Dialog ===== */
.dict-form :deep(.el-form-item__label) {
  font-weight: 500;
}

.full-width {
  width: 100%;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>