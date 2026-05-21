<template>
  <section class="case-stat-cards">
    <article
      v-for="card in cards"
      :key="card.key"
      class="case-stat-card"
      :class="{ 'case-stat-card--active': card.active }"
    >
      <div class="case-stat-card__top">
        <span>{{ card.title }}</span>
        <el-icon><component :is="card.icon" /></el-icon>
      </div>
      <strong>{{ card.value }}</strong>
      <small :class="card.trendClass">{{ card.trend }}</small>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Connection, DataLine, Finished, Files } from '@element-plus/icons-vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({}),
  },
  activeType: {
    type: String,
    default: 'api',
  },
})

const cards = computed(() => {
  const total = props.stats.total || 0
  const apiTotal = props.stats.api_total || 0
  const functionalTotal = props.stats.functional_total || 0
  const coverage = props.stats.coverage || 0
  return [
    {
      key: 'total',
      title: '总用例数',
      value: total,
      trend: `当前视图 ${props.stats.current_total || 0}`,
      icon: Files,
    },
    {
      key: 'api',
      title: '接口用例数',
      value: apiTotal,
      trend: `占比 ${formatPercent(apiTotal, total)}`,
      active: props.activeType === 'api',
      icon: Connection,
    },
    {
      key: 'functional',
      title: '功能用例数',
      value: functionalTotal,
      trend: `占比 ${formatPercent(functionalTotal, total)}`,
      active: props.activeType === 'functional',
      icon: Finished,
    },
    {
      key: 'coverage',
      title: '自动化覆盖率',
      value: `${coverage}%`,
      trend: `已自动化 ${props.stats.automated || 0}`,
      trendClass: 'is-success',
      icon: DataLine,
    },
  ]
})

function formatPercent(value, total) {
  if (!total) return '0%'
  return `${((value / total) * 100).toFixed(1)}%`
}
</script>

<style scoped>
.case-stat-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.case-stat-card {
  position: relative;
  min-height: 92px;
  padding: 14px 16px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(145deg, rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.5)),
    rgba(20, 22, 27, 0.58);
  box-shadow: 0 18px 42px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.055);
  backdrop-filter: blur(18px) saturate(1.2);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

html:not(.dark) .case-stat-card {
  border-color: rgba(22, 119, 255, 0.14);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.84), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 40px rgba(20, 42, 76, 0.09), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

.case-stat-card::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.08), transparent 34%),
    linear-gradient(90deg, rgba(56, 189, 248, 0.18), transparent 54%);
  opacity: 0.55;
  content: "";
}

.case-stat-card::after {
  position: absolute;
  inset: auto 14px 12px auto;
  width: 42px;
  height: 2px;
  border-radius: var(--border-radius-round);
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.86));
  content: "";
}

.case-stat-card:hover,
.case-stat-card--active {
  transform: translateY(-2px);
  border-color: rgba(56, 189, 248, 0.42);
  box-shadow: 0 18px 44px rgba(56, 189, 248, 0.14);
}

.case-stat-card__top {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.case-stat-card__top .el-icon {
  color: #38bdf8;
  font-size: 20px;
}

.case-stat-card strong {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 8px;
  color: var(--text-strong);
  font-family: var(--font-mono);
  font-size: 30px;
  line-height: 1;
}

.case-stat-card small {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.case-stat-card small.is-success {
  color: var(--color-success);
}

@media (max-width: 1180px) {
  .case-stat-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
