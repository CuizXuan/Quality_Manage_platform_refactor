<template>
  <div class="ai-prompt-templates-page">
    <!-- 页面标题区 -->
    <header class="ai-prompt-templates-page__header">
      <div>
        <h1>Prompt 模板管理</h1>
        <p>统一管理 AI 模型的 Prompt 模板，支持变体生成、断言生成等功能。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="handleCreate">新建模板</el-button>
    </header>

    <!-- 查询区 -->
    <section class="ai-prompt-templates-page__filters">
      <el-form :model="draftFilters" inline label-position="left" class="filter-form">
        <el-form-item label="模板类型" class="filter-item">
          <el-select
            v-model="draftFilters.template_type"
            placeholder="全部类型"
            clearable
            class="filter-control"
          >
            <el-option label="变体生成" value="variant_generation" />
            <el-option label="断言生成" value="assertion_generation" />
            <el-option label="失败分析" value="failure_analysis" />
            <el-option label="报告总结" value="report_summary" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词" class="filter-item">
          <el-input
            v-model="draftFilters.keyword"
            placeholder="搜索模板名称"
            clearable
            class="search-bar__input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item class="filter-item filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="ai-prompt-templates-page__table">
      <el-table
        v-loading="aiStore.loading"
        :data="aiStore.templates"
        height="100%"
        highlight-current-row
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="模板名称" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="template_type" label="类型" width="140" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ formatType(row.template_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="variables" label="变量" width="100" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ row.variables?.length || 0 }} 个</span>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="handleEdit(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的模板</span>
        </template>
      </el-table>

      <div class="ai-prompt-templates-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="aiStore.templateTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="formVisible"
      :title="isEdit ? '编辑模板' : '新建模板'"
      top="4vh"
      width="min(720px, 92vw)"
      destroy-on-close
      append-to-body
    >
      <el-form ref="formRef" :model="templateForm" :rules="formRules" label-width="130px" class="template-form">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="templateForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="模板类型" prop="template_type">
          <el-select v-model="templateForm.template_type" style="width: 100%">
            <el-option label="变体生成" value="variant_generation" />
            <el-option label="断言生成" value="assertion_generation" />
            <el-option label="失败分析" value="failure_analysis" />
            <el-option label="报告总结" value="report_summary" />
          </el-select>
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input
            v-model="templateForm.system_prompt"
            type="textarea"
            :rows="3"
            placeholder="System Prompt（可选）"
          />
        </el-form-item>
        <el-form-item label="User Prompt 模板" prop="user_prompt_template">
          <el-input
            v-model="templateForm.user_prompt_template"
            type="textarea"
            :rows="4"
            placeholder="使用 {{variable}} 占位符，例如 {{case_name}}、{{method}}、{{url}}"
          />
        </el-form-item>
        <el-form-item label="变量列表">
          <el-select
            v-model="templateForm.variables"
            multiple
            filterable
            allow-create
            placeholder="输入变量名后回车"
            style="width: 100%"
          >
            <el-option v-for="v in templateForm.variables" :key="v" :label="v" :value="v" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="templateForm.enabled" />
        </el-form-item>

        <!-- 变量预览 -->
        <el-form-item v-if="templateForm.variables.length > 0" label="变量预览">
          <div class="variable-preview">
            <code>{{ renderPreview(templateForm.user_prompt_template) }}</code>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleFormSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAiStore } from '@/stores/aiStore'

const aiStore = useAiStore()

const isEdit = ref(false)
const saving = ref(false)
const formRef = ref(null)
const currentTemplate = ref(null)
const formVisible = ref(false)

const draftFilters = ref({
  keyword: '',
  template_type: '',
})

const appliedFilters = ref({
  keyword: '',
  template_type: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const templateForm = ref({
  name: '',
  description: '',
  template_type: 'variant_generation',
  system_prompt: '',
  user_prompt_template: '',
  variables: [],
  enabled: true,
})

const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  template_type: [{ required: true, message: '请选择模板类型', trigger: 'change' }],
  user_prompt_template: [{ required: true, message: '请输入 User Prompt 模板', trigger: 'blur' }],
}

onMounted(() => {
  aiStore.fetchTemplates({ page: 1, page_size: pagination.value.pageSize })
})

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.template_type && { template_type: appliedFilters.value.template_type }),
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  aiStore.fetchTemplates({ ...buildQueryParams(), page: 1 })
}

function handleReset() {
  draftFilters.value = { keyword: '', template_type: '' }
  appliedFilters.value = { keyword: '', template_type: '' }
  pagination.value.page = 1
  aiStore.fetchTemplates({ page: 1, page_size: pagination.value.pageSize })
}

function handlePageChange(page) {
  pagination.value.page = page
  aiStore.fetchTemplates({ ...buildQueryParams(), page })
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  aiStore.fetchTemplates({ ...buildQueryParams(), page: 1, page_size: size })
}

function handleCreate() {
  isEdit.value = false
  currentTemplate.value = null
  templateForm.value = {
    name: '',
    description: '',
    template_type: 'variant_generation',
    system_prompt: '',
    user_prompt_template: '',
    variables: [],
    enabled: true,
  }
  formVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  currentTemplate.value = row
  templateForm.value = {
    name: row.name || '',
    description: row.description || '',
    template_type: row.template_type || 'variant_generation',
    system_prompt: row.system_prompt || '',
    user_prompt_template: row.user_prompt_template || '',
    variables: row.variables || [],
    enabled: row.enabled !== false,
  }
  formVisible.value = true
}

async function handleFormSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await aiStore.updateTemplate(currentTemplate.value.id, templateForm.value)
      ElMessage.success('更新成功')
    } else {
      await aiStore.createTemplate(templateForm.value)
      ElMessage.success('创建成功')
    }
    formVisible.value = false
    aiStore.fetchTemplates(buildQueryParams())
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除模板「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await aiStore.deleteTemplate(row.id)
    ElMessage.success('删除成功')
    aiStore.fetchTemplates(buildQueryParams())
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function formatType(type) {
  const map = {
    variant_generation: '变体生成',
    assertion_generation: '断言生成',
    failure_analysis: '失败分析',
    report_summary: '报告总结',
  }
  return map[type] || type
}

function renderPreview(template) {
  if (!template) return ''
  return template.replace(/\{(\w+)\}/g, '<$1>')
}
</script>

<style scoped>
/* ── 动画关键帧 ── */
@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes case-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

/* ── 页面容器 ── */
.ai-prompt-templates-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
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
  position: relative;
}

.ai-prompt-templates-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.ai-prompt-templates-page::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: case-particles 18s ease-in-out infinite alternate;
}

html:not(.dark) .ai-prompt-templates-page {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(14, 116, 144, 0.12), transparent 30%),
    linear-gradient(225deg, rgba(22, 119, 255, 0.16), transparent 36%),
    linear-gradient(0deg, rgba(56, 189, 248, 0.08), transparent 50%),
    var(--bg-page);
}

/* ── 标题区 ── */
.ai-prompt-templates-page__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
  z-index: 1;
}

.ai-prompt-templates-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .ai-prompt-templates-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

.ai-prompt-templates-page__header h1,
.ai-prompt-templates-page__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

.ai-prompt-templates-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.ai-prompt-templates-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.btn-primary-add {
  position: relative;
  z-index: 1;
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
.ai-prompt-templates-page__filters {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.58);
  background-size: 28px 28px, 28px 28px;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.ai-prompt-templates-page__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .ai-prompt-templates-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.72);
  background-size: 28px 28px, 28px 28px;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .ai-prompt-templates-page__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%);
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-size: 13px;
}

.filter-item {
  display: inline-flex;
  align-items: center;
}

.filter-actions {
  margin-left: auto;
}

.filter-control {
  width: 160px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

.search-bar__input {
  width: 320px;
}

/* ── 表格区 ── */
.ai-prompt-templates-page__table {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.48);
  background-size: 32px 32px, 32px 32px;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.ai-prompt-templates-page__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-table-scan 12s linear infinite;
}

html:not(.dark) .ai-prompt-templates-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.64);
  background-size: 32px 32px, 32px 32px;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .ai-prompt-templates-page__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
}

.ai-prompt-templates-page__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-row-hover-bg-color: rgba(56, 189, 248, 0.1);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .ai-prompt-templates-page__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

.ai-prompt-templates-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.ai-prompt-templates-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.ai-prompt-templates-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.ai-prompt-templates-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .ai-prompt-templates-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

/* ── 通用 ── */
.name-cell {
  font-weight: 600;
  color: var(--text-primary);
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
.template-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.variable-preview {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  padding: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  max-height: 80px;
  overflow-y: auto;
}

.variable-preview code {
  font-family: var(--font-mono);
}

@media (prefers-reduced-motion: reduce) {
  .ai-prompt-templates-page::before,
  .ai-prompt-templates-page::after,
  .ai-prompt-templates-page__header::after,
  .ai-prompt-templates-page__filters::before,
  .ai-prompt-templates-page__table::before {
    animation: none;
  }
}
</style>
