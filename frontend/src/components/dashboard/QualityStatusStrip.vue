<template>
  <div class="quality-status-strip">
    <div class="kpi-item" v-for="kpi in kpis" :key="kpi.label">
      <span class="kpi-label">{{ kpi.label }}</span>
      <span class="kpi-value" :class="kpi.class">{{ kpi.value }}</span>
      <span v-if="kpi.trend" class="kpi-trend" :class="kpi.trend > 0 ? 'up' : 'down'">
        {{ kpi.trend > 0 ? '↑' : '↓' }} {{ Math.abs(kpi.trend) }}%
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      passRate: 0,
      failCount: 0,
      blockDefects: 0,
      avgDuration: 0,
      robustnessScore: 0,
      recentSuccessRate: 0,
    }),
  },
})

const kpis = computed(() => [
  {
    label: '通过率',
    value: `${props.stats.passRate}%`,
    class: props.stats.passRate >= 90 ? 'success' : props.stats.passRate >= 70 ? 'warning' : 'danger',
  },
  {
    label: '失败',
    value: props.stats.failCount,
    class: props.stats.failCount > 0 ? 'danger' : '',
  },
  {
    label: '阻断缺陷',
    value: props.stats.blockDefects,
    class: props.stats.blockDefects > 0 ? 'danger' : '',
  },
  {
    label: '平均耗时',
    value: `${props.stats.avgDuration}ms`,
    class: props.stats.avgDuration > 1000 ? 'warning' : '',
  },
  {
    label: '健壮性',
    value: props.stats.robustnessScore > 0 ? `${props.stats.robustnessScore}/100` : '-',
    class: props.stats.robustnessScore >= 80 ? 'success' : props.stats.robustnessScore >= 60 ? 'warning' : 'danger',
  },
  {
    label: '调试成功率',
    value: `${props.stats.recentSuccessRate}%`,
    class: props.stats.recentSuccessRate >= 90 ? 'success' : props.stats.recentSuccessRate >= 70 ? 'warning' : 'danger',
  },
])
</script>

<style scoped>
.quality-status-strip {
  display: flex;
  gap: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
}

.kpi-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-right: 1px solid var(--el-border-color-lighter);
}

.kpi-item:last-child {
  border-right: none;
}

.kpi-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.kpi-value {
  font-size: 18px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.kpi-value.success { color: var(--el-color-success); }
.kpi-value.warning { color: var(--el-color-warning); }
.kpi-value.danger { color: var(--el-color-danger); }

.kpi-trend {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
}

.kpi-trend.up { color: var(--el-color-success); }
.kpi-trend.down { color: var(--el-color-danger); }
</style>