<template>
  <section class="case-table-panel">
    <div v-if="selectedRows.length" class="case-table-panel__bulk">
      <span>已选择 {{ selectedRows.length }} 条</span>
      <el-button size="small" type="success" @click="emit('batch-automated', true)">批量标记自动化</el-button>
      <el-button size="small" @click="emit('batch-priority')">批量修改优先级</el-button>
      <el-button size="small" type="danger" @click="emit('batch-delete')">批量删除</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="items"
      height="100%"
      row-key="id"
      @selection-change="emit('selection-change', $event)"
      @row-dblclick="emit('edit', $event)"
    >
      <el-table-column type="selection" width="42" fixed="left" />

      <el-table-column prop="auto_case_id" label="编号" width="162" fixed="left">
        <template #default="{ row }">
          <OverflowText :text="displayCaseCode(row)" class="case-table-panel__code" mono />
        </template>
      </el-table-column>

      <el-table-column prop="name" label="用例名称" min-width="190" fixed="left">
        <template #default="{ row }">
          <OverflowText
            :text="row.name"
            as="button"
            class="case-table-panel__name"
            primary
            strong
            @click.stop="emit('edit', row)"
          />
        </template>
      </el-table-column>

      <el-table-column
        v-if="caseType === 'api'"
        class-name="case-table-panel__method-column"
        label-class-name="case-table-panel__method-header"
        label="Method"
        width="84"
        sortable
        align="center"
      >
        <template #default="{ row }">
          <span class="method-badge" :class="apiCase(row).method.toLowerCase()">
            {{ apiCase(row).method }}
          </span>
        </template>
      </el-table-column>

      <el-table-column v-if="caseType === 'api'" label="URL" min-width="260" sortable>
        <template #default="{ row }">
          <OverflowText :text="apiCase(row).url" mono />
        </template>
      </el-table-column>

      <el-table-column v-if="caseType === 'api'" label="描述" min-width="220">
        <template #default="{ row }">
          <OverflowText :text="stripHtml(row.description)" muted />
        </template>
      </el-table-column>

      <el-table-column v-if="caseType === 'functional'" label="前置条件" min-width="240">
        <template #default="{ row }">
          <OverflowText :text="stripHtml(row.pre_condition)" />
        </template>
      </el-table-column>

      <el-table-column v-if="caseType === 'functional'" label="描述" min-width="190">
        <template #default="{ row }">
          <OverflowText :text="stripHtml(row.description)" muted />
        </template>
      </el-table-column>

      <el-table-column v-if="caseType === 'functional'" label="步骤数" width="84" align="center">
        <template #default="{ row }">{{ functionalCase(row).steps.length }} 步</template>
      </el-table-column>

      <el-table-column prop="priority" label="优先级" width="86" sortable align="center">
        <template #default="{ row }">
          <span class="priority-pill" :class="`priority-pill--${row.priority.toLowerCase()}`">
            {{ priorityIcon(row.priority) }} {{ row.priority }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="自动化" width="118" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_automated"
            inline-prompt
            active-text="已自动化"
            inactive-text="未自动化"
            @click.stop
            @change="emit('toggle-automated', row, $event)"
          />
        </template>
      </el-table-column>

      <el-table-column prop="updated_at" label="更新时间" width="150" sortable>
        <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
      </el-table-column>

      <el-table-column label="创建人" width="96">
        <template #default="{ row }">
          <OverflowText :text="row.creator_name || row.created_by" />
        </template>
      </el-table-column>

      <el-table-column label="操作" width="136" fixed="right" align="center">
        <template #default="{ row }">
          <div class="case-table-panel__actions">
            <el-button text type="primary" @click.stop="emit('edit', row)">编辑</el-button>
            <el-button text type="primary" @click.stop="emit('copy', row)">复制</el-button>
            <el-button text type="danger" @click.stop="emit('delete', row)">删除</el-button>
          </div>
        </template>
      </el-table-column>

      <template #empty>
        <div class="case-table-panel__empty">
          <div class="case-table-panel__empty-mark"></div>
          <span>暂无符合条件的用例</span>
        </div>
      </template>
    </el-table>
  </section>
</template>

<script setup>
import OverflowText from '@/components/common/OverflowText.vue'
import { formatDateTime, stripHtml } from './caseUtils'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  selectedRows: {
    type: Array,
    default: () => [],
  },
  caseType: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'selection-change',
  'edit',
  'delete',
  'copy',
  'toggle-automated',
  'batch-automated',
  'batch-priority',
  'batch-delete',
])

function apiCase(row) {
  return row.api_case || {
    method: row.method || 'GET',
    url: row.url || '',
  }
}

function functionalCase(row) {
  return row.functional_case || {
    steps: [],
  }
}

function priorityIcon(priority) {
  const map = {
    P0: '●',
    P1: '●',
    P2: '●',
    P3: '○',
  }
  return map[priority] || '○'
}

function displayCaseCode(row) {
  return row.auto_case_id || `#${row.id}`
}
</script>

<style scoped>
.case-table-panel {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
}

.case-table-panel::before {
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

.case-table-panel :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  position: relative;
  z-index: 1;
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .case-table-panel :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

.case-table-panel :deep(.el-table__inner-wrapper::before) {
  background: rgba(56, 189, 248, 0.12);
}

.case-table-panel :deep(.el-table__body-wrapper),
.case-table-panel :deep(.el-table__header-wrapper),
.case-table-panel :deep(.el-scrollbar__view) {
  background: transparent;
}

.case-table-panel__bulk {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color-lighter);
  background: var(--color-primary-soft);
}

.case-table-panel__bulk span {
  margin-right: auto;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 700;
}

.case-table-panel__code {
  min-width: 0;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.case-table-panel__name {
  min-width: 0;
  font-weight: 700;
}

.case-table-panel :deep(.el-table__header th) {
  height: 44px;
  color: var(--text-secondary);
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  font-weight: 700;
}

.case-table-panel :deep(.el-table .cell) {
  padding: 0 10px;
}

.case-table-panel :deep(.case-table-panel__method-header .cell) {
  display: inline-flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 2px;
  white-space: nowrap;
}

.case-table-panel :deep(.case-table-panel__method-header .caret-wrapper) {
  flex: 0 0 auto;
  width: 12px;
  margin-left: 0;
}

.case-table-panel :deep(.el-table__body td) {
  height: 48px;
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.case-table-panel :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .case-table-panel :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.case-table-panel :deep(.el-table__row > td.el-table__cell) {
  transition: background 0.2s ease;
}

.case-table-panel :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--color-primary-soft) !important;
  background-color: var(--color-primary-soft) !important;
}

@keyframes case-table-scan {
  from { transform: translateX(-22%); }
  to { transform: translateX(22%); }
}

@media (prefers-reduced-motion: reduce) {
  .case-table-panel::before {
    animation: none;
  }
}

.case-table-panel :deep(.el-table__row:hover > td.el-table-fixed-column--left),
.case-table-panel :deep(.el-table__row:hover > td.el-table-fixed-column--right) {
  background: var(--color-primary-soft) !important;
  background-color: var(--color-primary-soft) !important;
}

.case-table-panel :deep(.method-badge) {
  min-width: 48px;
  height: 24px;
  padding: 0 10px;
  border-radius: var(--border-radius-base);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

.case-table-panel__actions {
  display: inline-flex;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}

.case-table-panel__actions :deep(.el-button) {
  margin-left: 0;
  padding: 0 3px;
  font-size: 12px;
}

.priority-pill {
  display: inline-flex;
  min-width: 48px;
  justify-content: center;
  gap: 4px;
  border-radius: var(--border-radius-round);
  font-size: 12px;
  font-weight: 800;
}

.priority-pill--p0 {
  color: var(--color-danger);
}

.priority-pill--p1 {
  color: var(--color-warning);
}

.priority-pill--p2 {
  color: var(--color-primary);
}

.priority-pill--p3 {
  color: var(--text-secondary);
}

.case-table-panel__empty {
  display: grid;
  gap: 10px;
  place-items: center;
  padding: 44px 0;
  color: var(--text-secondary);
}

.case-table-panel__empty-mark {
  width: 80px;
  height: 46px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(90deg, transparent 0 18%, rgba(56, 189, 248, 0.18) 18% 22%, transparent 22%),
    repeating-linear-gradient(0deg, var(--bg-container-soft) 0 9px, transparent 9px 18px);
}
</style>
