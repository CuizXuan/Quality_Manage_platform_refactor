<template>
  <div class="suggestion-history">
    <!-- 页面标题区 -->
    <header class="suggestion-history__header">
      <div>
        <h1>建议历史</h1>
        <p>查看 AI 建议采纳记录，支持按类型与状态筛选。</p>
      </div>
    </header>

    <!-- 筛选区 -->
    <section class="suggestion-history__filters">
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="采纳状态：" class="filter-item">
            <el-select
              v-model="draftFilters.accepted"
              placeholder="全部状态"
              clearable
              class="filter-control"
            >
              <el-option label="已采纳" value="true" />
              <el-option label="待采纳" value="false" />
            </el-select>
          </el-form-item>
          <el-form-item label="建议类型：" class="filter-item">
            <el-select
              v-model="draftFilters.suggestion_type"
              placeholder="全部类型"
              clearable
              class="filter-control"
            >
              <el-option label="修复建议" value="fix" />
              <el-option label="优化建议" value="optimization" />
              <el-option label="测试建议" value="test" />
              <el-option label="安全建议" value="security" />
            </el-select>
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="suggestion-history__table">
      <el-table
        v-loading="aiStore.loading"
        :data="suggestionList"
        height="100%"
        highlight-current-row
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="suggestion_type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getTypeTagType(row.suggestion_type)">
              {{ formatSuggestionType(row.suggestion_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="内容" min-width="300">
          <template #default="{ row }">
            <span class="content-preview" :title="formatContent(row.content)">
              {{ truncateContent(row.content) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="accepted" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.accepted ? 'success' : 'info'" size="small">
              {{ row.accepted ? '已采纳' : '待采纳' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accepted_at" label="采纳时间" width="160">
          <template #default="{ row }">{{ row.accepted_at || '—' }}</template>
        </el-table-column>
        <el-table-column prop="accepted_by" label="采纳人" width="120">
          <template #default="{ row }">{{ row.accepted_by || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="!row.accepted"
              type="primary"
              text
              size="small"
              @click.stop="handleAccept(row)"
            >
              采纳
            </el-button>
            <span v-else class="accepted-text">—</span>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无建议数据</span>
        </template>
      </el-table>

      <div v-if="suggestionList.length > 0" class="suggestion-history__pagination">
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

    <!-- 采纳对话框 -->
    <el-dialog v-model="acceptDialogVisible" title="采纳建议" width="400px" destroy-on-close>
      <el-form :model="acceptForm" label-width="80px">
        <el-form-item label="备注">
          <el-input
            v-model="acceptForm.comment"
            type="textarea"
            :rows="3"
            placeholder="请输入采纳备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="acceptDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="acceptLoading" @click="confirmAccept">确认采纳</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import feedback from '@/utils/feedback'
import { useAiStore } from '@/stores/aiStore'

const aiStore = useAiStore()

const suggestionList = ref([])
const total = ref(0)
const acceptDialogVisible = ref(false)
const acceptLoading = ref(false)
const acceptForm = reactive({ comment: '' })
const currentAcceptId = ref(null)

const draftFilters = ref({ accepted: '', suggestion_type: '' })
const appliedFilters = ref({ accepted: '', suggestion_type: '' })
const pagination = ref({ page: 1, pageSize: 20 })

onMounted(fetchSuggestions)

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.accepted !== '' && { accepted: appliedFilters.value.accepted === 'true' }),
    ...(appliedFilters.value.suggestion_type && { suggestion_type: appliedFilters.value.suggestion_type }),
  }
}

async function fetchSuggestions() {
  try {
    const response = await aiStore.fetchSuggestions(buildQueryParams())
    if (response?.items) {
      suggestionList.value = response.items
      total.value = response.total || 0
    } else if (response?.data?.items) {
      suggestionList.value = response.data.items
      total.value = response.data.total || 0
    } else {
      suggestionList.value = []
      total.value = 0
    }
  } catch (err) {
    feedback.error(err.message || '获取建议列表失败')
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  fetchSuggestions()
}

function handleReset() {
  draftFilters.value = { accepted: '', suggestion_type: '' }
  appliedFilters.value = { accepted: '', suggestion_type: '' }
  pagination.value.page = 1
  fetchSuggestions()
}

function handlePageChange(p) {
  pagination.value.page = p
  fetchSuggestions()
}

function handleSizeChange(s) {
  pagination.value.pageSize = s
  pagination.value.page = 1
  fetchSuggestions()
}

function handleAccept(row) {
  currentAcceptId.value = row.id
  acceptForm.comment = ''
  acceptDialogVisible.value = true
}

async function confirmAccept() {
  acceptLoading.value = true
  try {
    await aiStore.acceptSuggestion(currentAcceptId.value, acceptForm.comment)
    feedback.success('建议已采纳')
    acceptDialogVisible.value = false
    fetchSuggestions()
  } catch (err) {
    feedback.error(err.message || '采纳建议失败')
  } finally {
    acceptLoading.value = false
  }
}

function formatSuggestionType(type) {
  const map = { fix: '修复建议', optimization: '优化建议', test: '测试建议', security: '安全建议' }
  return map[type] || type || '未知'
}

function getTypeTagType(type) {
  const map = { fix: 'danger', optimization: 'warning', test: 'primary', security: 'success' }
  return map[type] || 'info'
}

function formatContent(content) {
  if (!content) return ''
  if (typeof content === 'string') {
    try { return JSON.stringify(JSON.parse(content), null, 2) } catch { return content }
  }
  try { return JSON.stringify(content, null, 2) } catch { return String(content) }
}

function truncateContent(content, maxLen = 100) {
  const str = formatContent(content)
  return str.length <= maxLen ? str : str.substring(0, maxLen) + '...'
}
</script>

<style scoped>
/* ── 页面容器 ── */
.suggestion-history {
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  flex-direction: column;
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
}

.suggestion-history::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.suggestion-history::after {
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

/* ── 标题区 ── */
.suggestion-history__header {
  position: relative;
  z-index: 1;
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
}

.suggestion-history__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .suggestion-history__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.suggestion-history__header h1,
.suggestion-history__header p {
  margin: 0;
}

.suggestion-history__header h1 {
  position: relative;
  z-index: 1;
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.suggestion-history__header p {
  position: relative;
  z-index: 1;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 筛选区 ── */
.suggestion-history__filters {
  position: relative;
  z-index: 1;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.suggestion-history__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .suggestion-history__filters {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .suggestion-history__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-form__row {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
  width: 100%;
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
  display: inline-flex;
  align-items: center;
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

.filter-control {
  width: 160px;
}

/* ── 表格区 ── */
.suggestion-history__table {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.suggestion-history__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .suggestion-history__table {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .suggestion-history__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

.suggestion-history__table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  flex: 1;
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .suggestion-history__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

.suggestion-history__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.suggestion-history__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

html:not(.dark) .suggestion-history__table :deep(.el-table__row:hover > td) {
  background: rgba(22, 119, 255, 0.08) !important;
}

.suggestion-history__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.suggestion-history__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

/* ── 分页 ── */
.suggestion-history__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.1);
}

html:not(.dark) .suggestion-history__pagination {
  border-top-color: rgba(22, 119, 255, 0.1);
}

/* ── 通用 ── */
.content-preview {
  color: var(--text-primary);
  word-break: break-all;
  font-size: 13px;
}

.accepted-text {
  color: var(--text-secondary);
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-form-scan {
  from { transform: translateX(-20%); }
  to { transform: translateX(20%); }
}

@media (prefers-reduced-motion: reduce) {
  .suggestion-history::before,
  .suggestion-history::after,
  .suggestion-history__filters::before,
  .suggestion-history__table::before {
    animation: none;
  }
}
</style>
