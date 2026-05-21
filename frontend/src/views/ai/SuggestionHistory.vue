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
      <div class="filter-row">
        <el-select
          v-model="draftFilters.accepted"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="已采纳" value="true" />
          <el-option label="待采纳" value="false" />
        </el-select>
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
        <div class="filter-actions">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>
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
          :page-sizes="[10, 20, 50, 100]"
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
    const response = await aiStore.fetchAnalysis(buildQueryParams())
    if (Array.isArray(response)) {
      suggestionList.value = response
    } else if (response?.items) {
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
  return JSON.stringify(content, null, 2)
}

function truncateContent(content, maxLen = 100) {
  const str = formatContent(content)
  return str.length <= maxLen ? str : str.substring(0, maxLen) + '...'
}
</script>

<style scoped>
/* ── 页面容器 ── */
.suggestion-history {
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
.suggestion-history__header {
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

html:not(.dark) .suggestion-history__header {
  background: rgba(255, 255, 255, 0.86);
}

.suggestion-history__header h1,
.suggestion-history__header p {
  margin: 0;
}

.suggestion-history__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.suggestion-history__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 筛选区 ── */
.suggestion-history__filters {
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .suggestion-history__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-control {
  width: 160px;
}

.filter-actions {
  display: flex;
  gap: 12px;
}

/* ── 表格区 ── */
.suggestion-history__table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .suggestion-history__table {
  background: rgba(255, 255, 255, 0.86);
}

.suggestion-history__table :deep(.el-table) {
  flex: 1;
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

.suggestion-history__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.suggestion-history__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
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
</style>
