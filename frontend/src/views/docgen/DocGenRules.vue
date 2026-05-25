<template>
  <div class="docgen-rules-page page-shell page-shell--tech-grid">
    <!-- 页面标题区 -->
    <header class="docgen-rules-page__header">
      <div>
        <h1>规则管理</h1>
        <p>管理文档生成的规则配置</p>
      </div>
      <el-button type="primary" :icon="Plus" class="btn-primary-add" @click="showRuleDialog('create')">新增规则</el-button>
    </header>

    <!-- 查询区 -->
    <section class="docgen-rules-page__filters">
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="文档类型：" class="filter-item">
            <el-select v-model="draftFilters.doc_type" placeholder="文档类型" clearable class="filter-control">
              <el-option label="需求大纲" value="requirement_outline" />
              <el-option label="需求详情" value="requirement_detail" />
              <el-option label="数据库设计" value="database_design" />
              <el-option label="接口设计" value="api_design" />
            </el-select>
          </el-form-item>
          <el-form-item label="启用状态：" class="filter-item">
            <el-select v-model="draftFilters.enabled" placeholder="启用状态" clearable class="filter-control">
              <el-option label="已启用" :value="true" />
              <el-option label="已禁用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词：" class="filter-item filter-item--keyword">
            <el-input v-model="draftFilters.keyword" placeholder="搜索名称/文件名" clearable class="keyword-input" @keyup.enter="handleSearch" />
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="docgen-rules-page__table">
      <el-table v-loading="docgenStore.loading" :data="docgenStore.rules" height="100%" highlight-current-row stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="规则名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="doc_type" label="文档类型" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ formatDocType(row.doc_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="enabled" label="启用" width="80" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="showRuleDialog('edit', row)">编辑</el-button>
            <el-button type="danger" size="small" link @click="handleDeleteRule(row.id)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的规则</span>
        </template>
      </el-table>

      <div class="docgen-rules-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="docgenStore.ruleTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 规则编辑弹窗 -->
    <el-dialog
      v-model="ruleDialogVisible"
      :title="ruleDialogTitle"
      top="4vh"
      width="min(720px, 92vw)"
      destroy-on-close
      append-to-body
      :close-on-click-modal="false"
      class="docgen-rule-dialog"
    >
      <el-form ref="ruleFormRef" :model="ruleForm" label-width="100px" class="rule-form">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleForm.name" placeholder="如：概要设计规则" style="width: 100%" />
        </el-form-item>
        <el-form-item label="文档类型" prop="doc_type">
          <el-select v-model="ruleForm.doc_type" placeholder="选择文档类型" style="width: 100%">
            <el-option label="需求大纲" value="requirement_outline" />
            <el-option label="需求详情" value="requirement_detail" />
            <el-option label="数据库设计" value="database_design" />
            <el-option label="接口设计" value="api_design" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件名" prop="filename">
          <el-input v-model="ruleForm.filename" placeholder="如：概要设计.json" style="width: 100%" />
        </el-form-item>
        <el-form-item label="规则内容" prop="content">
          <el-input
            v-model="ruleForm.content"
            type="textarea"
            :rows="8"
            placeholder='JSON 格式的规则内容，如：{"structures": [...]}'
            class="json-textarea"
          />
        </el-form-item>
        <el-form-item label="启用规则">
          <el-switch v-model="ruleForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="ruleSaving" @click="handleSaveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDocgenStore } from '@/stores/docgenStore'

const docgenStore = useDocgenStore()

const draftFilters = ref({
  doc_type: '',
  enabled: '',
  keyword: '',
})

const appliedFilters = ref({
  doc_type: '',
  enabled: '',
  keyword: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const ruleDialogVisible = ref(false)
const ruleDialogTitle = ref('')
const ruleFormRef = ref(null)
const ruleSaving = ref(false)
const editingRuleId = ref(null)

const ruleForm = ref({
  name: '',
  doc_type: '',
  filename: '',
  content: '',
  enabled: true,
})

onMounted(() => {
  loadRules()
})

function loadRules() {
  docgenStore.fetchRules({
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    doc_type: appliedFilters.value.doc_type || undefined,
    enabled: appliedFilters.value.enabled === '' ? undefined : appliedFilters.value.enabled,
    keyword: appliedFilters.value.keyword || undefined,
  })
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  loadRules()
}

function handleReset() {
  draftFilters.value = { doc_type: '', enabled: '', keyword: '' }
  appliedFilters.value = { doc_type: '', enabled: '', keyword: '' }
  pagination.value.page = 1
  loadRules()
}

function handlePageChange() {
  loadRules()
}

function handleSizeChange() {
  pagination.value.page = 1
  loadRules()
}

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function formatDocType(docType) {
  const map = {
    requirement_outline: '需求大纲',
    requirement_detail: '需求详情',
    database_design: '数据库设计',
    api_design: '接口设计',
  }
  return map[docType] || docType
}

function showRuleDialog(mode, row = null) {
  if (mode === 'create') {
    ruleDialogTitle.value = '新增规则'
    editingRuleId.value = null
    ruleForm.value = { name: '', doc_type: '', filename: '', content: '', enabled: true }
  } else {
    ruleDialogTitle.value = '编辑规则'
    editingRuleId.value = row.id
    ruleForm.value = { name: row.name, doc_type: row.doc_type, filename: row.filename, content: row.content, enabled: row.enabled }
  }
  ruleDialogVisible.value = true
}

async function handleSaveRule() {
  ruleSaving.value = true
  try {
    if (editingRuleId.value) {
      await docgenStore.updateRule(editingRuleId.value, ruleForm.value)
      ElMessage.success('规则已更新')
    } else {
      await docgenStore.createRule(ruleForm.value)
      ElMessage.success('规则已创建')
    }
    ruleDialogVisible.value = false
    loadRules()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    ruleSaving.value = false
  }
}

async function handleToggleRule(row) {
  try {
    await docgenStore.updateRule(row.id, { enabled: row.enabled })
    ElMessage.success('已更新启用状态')
  } catch (err) {
    row.enabled = !row.enabled
    ElMessage.error('更新失败')
  }
}

async function handleDeleteRule(id) {
  await ElMessageBox.confirm('确定要删除该规则吗？', '警告', { type: 'warning' })
  await docgenStore.deleteRule(id)
  ElMessage.success('规则已删除')
  loadRules()
}
</script>

<style scoped>
.docgen-rules-page {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
}

.docgen-rules-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  padding: 14px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.docgen-rules-page__header h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.docgen-rules-page__header p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.docgen-rules-page__filters {
  flex-shrink: 0;
  padding: 12px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.filter-form {
  width: 100%;
}

.filter-form__row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-item {
  margin-bottom: 0;
}

.filter-item :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.filter-item--keyword {
  width: 200px;
}

.filter-control {
  width: 160px;
}

.keyword-input {
  width: 200px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-actions .el-button {
  min-width: 76px;
  height: 34px;
}

.docgen-rules-page__table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
  padding: 12px 16px;
  overflow: hidden;
}

.docgen-rules-page__table .el-table {
  flex: 1;
  min-height: 0;
}

.docgen-rules-page__pagination {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.json-textarea {
  font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  font-size: 13px;
}

.rule-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}
</style>
