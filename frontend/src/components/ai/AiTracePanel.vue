<template>
  <div class="ai-trace-panel" :class="{ 'is-compact': compact }">
    <div class="ai-trace-panel__header">
      <span class="ai-trace-panel__title">
        <el-icon><Connection /></el-icon>
        <span>{{ title || '关联 AI 工作流' }}</span>
      </span>
      <el-button
        v-if="items.length"
        text
        size="small"
        :icon="Refresh"
        :loading="loading"
        @click="reload"
      >刷新</el-button>
    </div>

    <div v-if="!validOrigin" class="ai-trace-panel__empty">
      <el-icon><InfoFilled /></el-icon>
      <span>未指定来源对象，无法查询关联 workflow。</span>
    </div>

    <div v-else-if="loading" class="ai-trace-panel__loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在查询关联 workflow…</span>
    </div>

    <div v-else-if="loadError" class="ai-trace-panel__empty">
      <el-icon><InfoFilled /></el-icon>
      <span>查询失败：{{ loadError }}</span>
    </div>

    <div v-else-if="!items.length" class="ai-trace-panel__empty">
      <el-icon><InfoFilled /></el-icon>
      <span>暂无关联 AI 工作流</span>
    </div>

    <ul v-else class="ai-trace-panel__list">
      <li v-for="run in items" :key="run.id" class="ai-trace-panel__item">
        <div class="ai-trace-panel__item-main">
          <div class="ai-trace-panel__item-title">
            <span class="ai-trace-panel__run-id">#{{ run.id }}</span>
            <span class="ai-trace-panel__workflow-type">{{ formatWorkflowType(run.workflow_type) }}</span>
            <el-tag :type="statusTagType(run.status)" size="small">{{ statusLabel(run.status) }}</el-tag>
          </div>
          <div class="ai-trace-panel__item-meta">
            <span>更新时间：{{ run.updated_at || run.created_at || '—' }}</span>
            <span v-if="run.steps && run.steps.length" class="ai-trace-panel__steps">
              步骤：
              <span
                v-for="step in run.steps"
                :key="step.id"
                class="ai-trace-panel__step-chip"
                :class="`step-${step.status}`"
              >{{ step.agent_type }}</span>
            </span>
          </div>
        </div>
        <el-button
          type="primary"
          text
          size="small"
          @click="openInWorkbench(run.id)"
        >查看</el-button>
      </li>
    </ul>

    <div v-if="validOrigin && !loading && !loadError && items.length" class="ai-trace-panel__footer">
      共 {{ total }} 条，最近展示 {{ items.length }} 条
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Connection, InfoFilled, Loading, Refresh } from '@element-plus/icons-vue'
import { useAiStore } from '@/stores/aiStore'

const props = defineProps({
  originModule: { type: String, default: '' },
  originType: { type: String, default: '' },
  originId: { type: Number, default: null },
  title: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})

const router = useRouter()
const aiStore = useAiStore()

// 七期 A 返工：组件局部状态；切换 origin / 失败时
// 不会再展示上一个 origin 的 workflow，避免溯源错位。
const localItems = ref([])
const localTotal = ref(0)
const localLoading = ref(false)
const loadError = ref('')
let inflightSeq = 0

const validOrigin = computed(
  () => !!props.originModule && !!props.originType && props.originId !== null && props.originId !== undefined,
)
const items = computed(() => localItems.value)
const total = computed(() => localTotal.value)
const loading = computed(() => localLoading.value)

async function load() {
  if (!validOrigin.value) {
    // 缺参：清空当前面板的本地态，回到"未指定来源"
    localItems.value = []
    localTotal.value = 0
    localLoading.value = false
    loadError.value = ''
    return
  }
  const seq = ++inflightSeq
  // 关键：发起新请求前，先清空当前面板的本地态；
  // 这样在 B 请求 in-flight 时，面板一定处于"加载中 / 空态"，
  // 不会展示上一个 origin 的数据。
  localItems.value = []
  localTotal.value = 0
  localLoading.value = true
  loadError.value = ''
  try {
    const result = await aiStore.fetchWorkflowTrace({
      origin_module: props.originModule,
      origin_type: props.originType,
      origin_id: Number(props.originId),
      limit: 5,
    })
    // 防止更晚的请求覆盖更早的请求
    if (seq !== inflightSeq) return
    localItems.value = result?.items || []
    localTotal.value = result?.total || 0
  } catch (e) {
    if (seq !== inflightSeq) return
    localItems.value = []
    localTotal.value = 0
    loadError.value = e?.response?.data?.detail || e?.message || '查询失败'
  } finally {
    if (seq === inflightSeq) {
      localLoading.value = false
    }
  }
}

function reload() {
  load()
}

function openInWorkbench(runId) {
  router.push({ path: '/ai/workbench', query: { run_id: runId } })
}

function formatWorkflowType(type) {
  if (!type) return 'workflow'
  if (type === 'requirement_to_test_design') return '需求到测试设计'
  return type
}

function statusTagType(status) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running') return 'warning'
  return 'info'
}

function statusLabel(status) {
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'running') return '运行中'
  if (status === 'pending') return '待启动'
  return status || '未知'
}

onMounted(load)
watch(
  () => [props.originModule, props.originType, props.originId],
  () => {
    load()
  },
)
</script>

<style scoped>
.ai-trace-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 32px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.ai-trace-panel.is-compact {
  padding: 8px 10px;
  gap: 6px;
}

.ai-trace-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-strong);
}

.ai-trace-panel__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #38bdf8;
}

.ai-trace-panel__empty,
.ai-trace-panel__loading {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.ai-trace-panel__empty .el-icon,
.ai-trace-panel__loading .el-icon {
  font-size: 16px;
}

.ai-trace-panel__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-trace-panel__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(56, 189, 248, 0.12);
  border-radius: var(--border-radius-sm);
  background: rgba(56, 189, 248, 0.04);
  transition: background 0.2s ease, border-color 0.2s ease;
}

.ai-trace-panel__item:hover {
  border-color: rgba(56, 189, 248, 0.32);
  background: rgba(56, 189, 248, 0.08);
}

.ai-trace-panel__item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ai-trace-panel__item-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-strong);
  font-size: 13px;
}

.ai-trace-panel__run-id {
  color: #38bdf8;
  font-weight: 700;
  font-family: var(--font-mono);
}

.ai-trace-panel__workflow-type {
  color: var(--text-secondary);
  font-size: 12px;
}

.ai-trace-panel__item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.ai-trace-panel__steps {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.ai-trace-panel__step-chip {
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.18);
}

.ai-trace-panel__step-chip.step-completed {
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.36);
  background: rgba(34, 197, 94, 0.12);
}

.ai-trace-panel__step-chip.step-failed {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.36);
  background: rgba(239, 68, 68, 0.12);
}

.ai-trace-panel__step-chip.step-running {
  color: #eab308;
  border-color: rgba(234, 179, 8, 0.36);
  background: rgba(234, 179, 8, 0.12);
}

.ai-trace-panel__footer {
  padding-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  text-align: right;
}

/* ── 浅色主题 ── */
html:not(.dark) .ai-trace-panel {
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.78), rgba(245, 250, 255, 0.62)),
    rgba(255, 255, 255, 0.62);
  border-color: rgba(22, 119, 255, 0.18);
  box-shadow: 0 12px 32px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

html:not(.dark) .ai-trace-panel__title {
  color: var(--color-primary);
}

html:not(.dark) .ai-trace-panel__item {
  background: rgba(255, 255, 255, 0.62);
  border-color: rgba(22, 119, 255, 0.12);
}

html:not(.dark) .ai-trace-panel__item:hover {
  background: rgba(240, 247, 255, 0.86);
  border-color: rgba(22, 119, 255, 0.28);
}

html:not(.dark) .ai-trace-panel__run-id {
  color: var(--color-primary);
}
</style>
