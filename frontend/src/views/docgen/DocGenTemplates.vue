<template>
  <div class="docgen-templates-page page-shell page-shell--tech-grid">
    <!-- 页面标题区 -->
    <header class="docgen-templates-page__header">
      <div>
        <h1>模板管理</h1>
        <p>上传和管理文档生成模板</p>
      </div>
      <div class="header-actions">
        <el-upload :auto-upload="false" :limit="1" accept=".docx" :on-change="handleTemplateFileChange">
          <el-button type="primary" class="btn-primary-add">选择文件</el-button>
        </el-upload>
        <el-button
          type="success"
          class="btn-success-action"
          :disabled="!pendingTemplateFile"
          :loading="uploading"
          @click="handleUploadTemplate"
        >
          确认上传
        </el-button>
      </div>
    </header>

    <!-- 查询区 -->
    <section class="docgen-templates-page__filters">
      <el-form :inline="false" :model="draftFilters" label-position="left" class="filter-form">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <el-form-item label="关键词：" class="filter-item filter-item--keyword">
              <el-input v-model="draftFilters.keyword" placeholder="搜索模板名称/文件名" clearable class="search-bar__input" @keyup.enter="handleSearch" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="docgen-templates-page__table">
      <el-table v-loading="docgenStore.loading" :data="docgenStore.templates" height="100%" highlight-current-row>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="模板名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="file_size" label="大小" width="100" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatFileSize(row.file_size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDeleteTemplate(row.id)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的模板</span>
        </template>
      </el-table>

      <div class="docgen-templates-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="docgenStore.templateTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDocgenStore } from '@/stores/docgenStore'

const docgenStore = useDocgenStore()

const draftFilters = ref({
  keyword: '',
})

const appliedFilters = ref({
  keyword: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const pendingTemplateFile = ref(null)
const uploading = ref(false)

onMounted(() => {
  loadTemplates()
})

function loadTemplates() {
  docgenStore.fetchTemplates({
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    keyword: appliedFilters.value.keyword || undefined,
  })
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  loadTemplates()
}

function handleReset() {
  draftFilters.value = { keyword: '' }
  appliedFilters.value = { keyword: '' }
  pagination.value.page = 1
  loadTemplates()
}

function handlePageChange() {
  loadTemplates()
}

function handleSizeChange() {
  pagination.value.page = 1
  loadTemplates()
}

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function formatFileSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleTemplateFileChange(file) {
  pendingTemplateFile.value = file.raw
}

async function handleUploadTemplate() {
  if (!pendingTemplateFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  try {
    await docgenStore.uploadTemplate(pendingTemplateFile.value)
    ElMessage.success('模板上传成功')
    pendingTemplateFile.value = null
    loadTemplates()
  } catch (err) {
    ElMessage.error(err.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleDeleteTemplate(id) {
  await ElMessageBox.confirm('确定要删除该模板吗？', '警告', { type: 'warning' })
  await docgenStore.deleteTemplate(id)
  ElMessage.success('模板已删除')
  loadTemplates()
}
</script>

<style scoped>
.docgen-templates-page {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
}

.docgen-templates-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  padding: 14px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.docgen-templates-page__header h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.docgen-templates-page__header p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-actions :deep(.el-upload) {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  height: 36px;
}

.header-actions :deep(.el-button),
.header-actions > .el-button {
  min-width: 96px;
  height: 36px;
}

.header-actions :deep(.el-upload-list) {
  display: none;
}

.btn-primary-add {
  border: 0;
  background: var(--brand-gradient);
  color: var(--text-inverse);
  font-weight: 700;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
}

/* ── Light Theme ── */
html:not(.dark) .docgen-templates-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .docgen-templates-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .docgen-templates-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .docgen-templates-page__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .docgen-templates-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .docgen-templates-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

.btn-success-action {
  color: var(--text-inverse);
  font-weight: 700;
}

.docgen-templates-page__filters {
  flex-shrink: 0;
  padding: 12px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.filter-form {
  width: 100%;
}

.filter-form :deep(.el-row) {
  align-items: flex-end;
  row-gap: 8px;
}

.filter-item {
  margin-bottom: 0;
  width: 100%;
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

.search-bar__input {
  width: 280px;
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

.docgen-templates-page__table {
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

.docgen-templates-page__table .el-table {
  flex: 1;
  min-height: 0;
}

.docgen-templates-page__pagination {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
