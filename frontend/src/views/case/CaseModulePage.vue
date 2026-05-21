<template>
  <div class="case-module">
    <aside class="case-module__aside">
      <CaseSidebar
        ref="sidebarRef"
        :case-type="caseType"
        :title="config.categoryTitle"
        :subtitle="config.categorySubtitle"
        @folder-selected="selectFolder"
      />
    </aside>

    <main class="case-module__main">
      <section class="case-module__filters">
        <CaseFilterBar v-model="draftFilters" :case-type="caseType" />
        <CaseSearchBar
          v-model:keyword="draftFilters.keyword"
          :case-type="caseType"
          @search="searchCases"
          @reset="resetFilters"
          @create="createCase"
        />
      </section>

      <section class="case-module__table">
        <CaseTable
          :items="cases"
          :selected-rows="selectedRows"
          :case-type="caseType"
          :loading="loading"
          @selection-change="selectedRows = $event"
          @edit="editCase"
          @delete="deleteCase"
          @copy="copyCase"
          @toggle-automated="toggleAutomated"
          @batch-automated="batchAutomated"
          @batch-priority="batchPriority"
          @batch-delete="batchDelete"
        />
        <CasePagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
        />
      </section>
    </main>

    <CaseEditDialog
      v-model="dialogVisible"
      :case-type="caseType"
      :case-data="currentCase"
      :folder-id="defaultFolderId"
      :suggested-case-id="suggestedCaseId"
      @saved="loadCases"
      @closed="currentCase = null"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { caseApi } from '@/api/case'
import feedback from '@/utils/feedback'
import CaseEditDialog from './CaseEditDialog.vue'
import CaseFilterBar from './CaseFilterBar.vue'
import CasePagination from './CasePagination.vue'
import CaseSearchBar from './CaseSearchBar.vue'
import CaseSidebar from './CaseSidebar.vue'
import CaseTable from './CaseTable.vue'
import { nextCaseCode } from './caseUtils'

const props = defineProps({
  caseType: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['stats-change'])

const cases = ref([])
const total = ref(0)
const stats = ref({})
const loading = ref(false)
const selectedRows = ref([])
const folderId = ref(null)
const sidebarRef = ref(null)
const dialogVisible = ref(false)
const currentCase = ref(null)
const draftFilters = ref(createFilters())
const appliedFilters = ref(createFilters())
const pagination = ref({
  page: 1,
  pageSize: 15,
})

const config = computed(() => {
  if (props.caseType === 'api') {
    return {
      categoryTitle: '接口分类',
      categorySubtitle: '按系统模块维护接口',
    }
  }
  return {
    categoryTitle: '功能分类',
    categorySubtitle: '按业务流程维护用例',
  }
})
const defaultFolderId = computed(() => folderId.value)
const suggestedCaseId = computed(() => nextCaseCode(props.caseType, cases.value, total.value))

function createFilters() {
  return {
    methods: [],
    priorities: [],
    isAutomated: null,
    createdRange: [],
    keyword: '',
  }
}

function buildQuery() {
  const range = appliedFilters.value.createdRange || []
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    case_type: props.caseType,
    keyword: appliedFilters.value.keyword || undefined,
    folder_id: folderId.value || undefined,
    methods: appliedFilters.value.methods?.length ? appliedFilters.value.methods : undefined,
    priorities: appliedFilters.value.priorities?.length ? appliedFilters.value.priorities : undefined,
    is_automated: appliedFilters.value.isAutomated ?? undefined,
    created_start: range[0] || undefined,
    created_end: range[1] || undefined,
  }
}

async function loadCases() {
  loading.value = true
  try {
    const response = await caseApi.list(buildQuery())
    cases.value = response.data.items || []
    total.value = response.data.total || 0
    stats.value = response.data.stats || {}
    selectedRows.value = []
    emit('stats-change', stats.value)
  } catch {
    feedback.error('用例列表加载失败')
  } finally {
    loading.value = false
  }
}

function searchCases() {
  appliedFilters.value = cloneFilters(draftFilters.value)
  pagination.value.page = 1
  loadCases()
}

function resetFilters() {
  draftFilters.value = createFilters()
  appliedFilters.value = createFilters()
  folderId.value = null
  sidebarRef.value?.reload()
  pagination.value.page = 1
  loadCases()
}

function cloneFilters(value) {
  return {
    methods: [...(value.methods || [])],
    priorities: [...(value.priorities || [])],
    isAutomated: value.isAutomated,
    createdRange: [...(value.createdRange || [])],
    keyword: value.keyword || '',
  }
}

function selectFolder(id) {
  folderId.value = id
  pagination.value.page = 1
  loadCases()
}

function createCase() {
  currentCase.value = null
  dialogVisible.value = true
}

async function editCase(row) {
  try {
    const response = await caseApi.get(row.id)
    currentCase.value = response.data
    dialogVisible.value = true
  } catch {
    feedback.error('用例详情加载失败')
  }
}

async function deleteCase(row) {
  try {
    await feedback.confirm(`确定删除用例「${row.name}」吗？`, '确认删除', { type: 'warning' })
    await caseApi.delete(row.id)
    feedback.success('用例删除成功')
    loadCases()
  } catch (error) {
    if (error !== 'cancel') feedback.error('用例删除失败')
  }
}

async function copyCase(row) {
  try {
    await caseApi.copy(row.id)
    feedback.success('用例复制成功')
    loadCases()
  } catch {
    feedback.error('用例复制失败')
  }
}

async function toggleAutomated(row, value) {
  try {
    await caseApi.update(row.id, { is_automated: value })
    row.is_automated = value
    loadCases()
  } catch {
    feedback.error('自动化状态更新失败')
  }
}

async function batchAutomated(value) {
  await runBatchUpdate({ is_automated: value }, '批量标记完成')
}

async function batchPriority() {
  if (!selectedRows.value.length) return
  try {
    const { value } = await ElMessageBox.prompt('请输入优先级：P0 / P1 / P2 / P3', '批量修改优先级', {
      inputPattern: /^P[0-3]$/,
      inputErrorMessage: '优先级只能是 P0、P1、P2、P3',
    })
    await runBatchUpdate({ priority: value }, '批量优先级更新完成')
  } catch (error) {
    if (error !== 'cancel') feedback.error('批量修改失败')
  }
}

async function batchDelete() {
  if (!selectedRows.value.length) return
  try {
    await feedback.confirm(`确定删除选中的 ${selectedRows.value.length} 条用例吗？`, '批量删除', { type: 'warning' })
    await caseApi.batchDelete(selectedRows.value.map((row) => row.id))
    feedback.success('批量删除完成')
    loadCases()
  } catch (error) {
    if (error !== 'cancel') feedback.error('批量删除失败')
  }
}

async function runBatchUpdate(data, message) {
  if (!selectedRows.value.length) return
  try {
    await caseApi.batchUpdate({
      ids: selectedRows.value.map((row) => row.id),
      ...data,
    })
    feedback.success(message)
    loadCases()
  } catch {
    feedback.error('批量更新失败')
  }
}

watch(
  () => [pagination.value.page, pagination.value.pageSize],
  ([page, pageSize], [oldPage, oldPageSize]) => {
    if (page !== oldPage && pageSize !== oldPageSize) return
    loadCases()
  },
)

watch(
  () => props.caseType,
  () => {
    draftFilters.value = createFilters()
    appliedFilters.value = createFilters()
    folderId.value = null
    pagination.value.page = 1
    loadCases()
  },
)

onMounted(() => {
  loadCases()
})
</script>

<style scoped>
.case-module {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 12px;
}

.case-module__aside,
.case-module__filters,
.case-module__table {
  position: relative;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 26px 26px, 26px 26px, auto, auto;
  box-shadow: 0 18px 42px rgba(2, 8, 23, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.055);
  backdrop-filter: blur(18px) saturate(1.2);
  overflow: hidden;
}

.case-module__aside::before,
.case-module__filters::before,
.case-module__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 38%, rgba(56, 189, 248, 0.1) 52%, transparent 68%),
    radial-gradient(circle at 86% 12%, rgba(34, 211, 166, 0.12), transparent 28%);
  opacity: 0.75;
  content: "";
}

.case-module__aside > *,
.case-module__filters > *,
.case-module__table > * {
  position: relative;
  z-index: 1;
}

html:not(.dark) .case-module__aside,
html:not(.dark) .case-module__filters,
html:not(.dark) .case-module__table {
  border-color: rgba(22, 119, 255, 0.14);
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  box-shadow: 0 18px 40px rgba(20, 42, 76, 0.09), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

.case-module__aside {
  min-width: 0;
  min-height: 0;
}

.case-module__main {
  display: flex;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  gap: 12px;
}

.case-module__filters {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 14px;
}

.case-module__table {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
}

@media (max-width: 1180px) {
  .case-module {
    grid-template-columns: 220px minmax(0, 1fr);
  }
}
</style>
