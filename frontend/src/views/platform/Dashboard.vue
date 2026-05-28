<template>
  <div class="dashboard-page">
    <section class="overview-strip">
      <div v-for="item in overviewItems" :key="item.label" class="overview-card">
        <div class="overview-icon" :class="item.tone">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <div>
          <span class="overview-label">{{ item.label }}</span>
          <strong :class="item.tone">{{ item.value }}</strong>
          <span class="overview-hint">{{ item.hint }}</span>
        </div>
      </div>
    </section>

    <section class="dashboard-grid">
      <div class="panel quality-trend">
        <div class="panel-head">
          <div>
            <span class="panel-kicker">Quality Trend</span>
            <h2>质量趋势</h2>
          </div>
          <div class="segmented">
            <button class="active" type="button">7天</button>
            <button type="button">14天</button>
            <button type="button">30天</button>
          </div>
        </div>
        <div class="trend-body">
          <div class="trend-chart">
            <div v-for="bar in trendBars" :key="bar.day" class="trend-column">
              <span class="bar success" :style="{ height: `${bar.pass}%` }"></span>
              <span class="bar danger" :style="{ height: `${bar.fail}%` }"></span>
              <small>{{ bar.day }}</small>
            </div>
          </div>
          <div class="trend-summary">
            <div class="summary-row">
              <span>平均通过率</span>
              <strong>{{ qualityStats.passRate }}%</strong>
            </div>
            <div class="summary-row">
              <span>平均耗时</span>
              <strong>{{ qualityStats.avgDuration }}ms</strong>
            </div>
            <div class="summary-row">
              <span>健壮性评分</span>
              <strong>{{ qualityStats.robustnessScore }}/100</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="panel gate-panel">
        <div class="panel-head compact">
          <div>
            <span class="panel-kicker">Quality Gate</span>
            <h2>质量门禁</h2>
          </div>
          <span class="gate-status warn">观察中</span>
        </div>
        <div class="gate-score">
          <strong>{{ gateScore }}</strong>
          <span>/100</span>
        </div>
        <div class="gate-progress">
          <span :style="{ width: `${gateScore}%` }"></span>
        </div>
        <div class="gate-rules">
          <div v-for="rule in gateRules" :key="rule.name" class="rule-row">
            <span class="rule-dot" :class="rule.status"></span>
            <span>{{ rule.name }}</span>
            <strong>{{ rule.value }}</strong>
          </div>
        </div>
      </div>

      <div class="panel quick-debug-panel">
        <div class="panel-head compact">
          <div>
            <span class="panel-kicker">Terminal</span>
            <h2>快捷调试</h2>
          </div>
          <el-button size="small" text @click="$router.push('/terminal')">完整调试台</el-button>
        </div>
        <TerminalQuickDebug />
      </div>

      <div class="panel recent-panel">
        <RecentDebug
          :items="recentDebugItems"
          :loading="debugLoading"
          :active-id="activeDebugId"
          @select="onSelectDebug"
          @refresh="loadHistory"
          @favorite="toggleFavorite"
          @unfavorite="toggleFavorite"
        />
      </div>

      <div class="panel action-panel">
        <div class="panel-head compact">
          <div>
            <span class="panel-kicker">Shortcuts</span>
            <h2>快捷入口</h2>
          </div>
        </div>
        <div class="quick-entry-grid">
          <button v-for="entry in quickEntries" :key="entry.label" class="entry-btn" type="button" @click="$router.push(entry.path)">
            <el-icon><component :is="entry.icon" /></el-icon>
            <span>{{ entry.label }}</span>
            <small>{{ entry.hint }}</small>
          </button>
        </div>
      </div>

      <div class="panel risk-panel">
        <div class="panel-head compact">
          <div>
            <span class="panel-kicker">Risk APIs</span>
            <h2>高频失败接口</h2>
          </div>
        </div>
        <div class="risk-list">
          <button v-for="item in riskItems" :key="item.url" class="risk-item" type="button">
            <span class="method-badge" :class="item.method.toLowerCase()">{{ item.method }}</span>
            <span class="risk-url">{{ item.url }}</span>
            <strong>{{ item.status }}</strong>
          </button>
        </div>
      </div>

      <div class="panel favorite-panel">
        <FavoriteRequests
          :items="favoriteItems"
          :loading="favoritesLoading"
          @select="onSelectDebug"
          @send="quickSend"
          @unfavorite="toggleFavorite"
        />
      </div>

      <div class="panel ai-panel">
        <div class="panel-head compact">
          <div>
            <span class="panel-kicker">AI Suggestions</span>
            <h2>AI 建议</h2>
          </div>
        </div>
        <div class="ai-list">
          <div v-for="item in aiSuggestions" :key="item.title" class="ai-item">
            <span class="suggestion-priority" :class="item.level">{{ item.levelText }}</span>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  CircleCheckFilled,
  Connection,
  DataBoard,
  Document,
  Histogram,
  MagicStick,
  Monitor,
  TrendCharts,
  VideoPlay,
  WarnTriangleFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { terminalApi } from '@/api/terminal'
import RecentDebug from '@/components/dashboard/widgets/RecentDebug.vue'
import TerminalQuickDebug from '@/components/dashboard/widgets/TerminalQuickDebug.vue'
import FavoriteRequests from '@/components/dashboard/widgets/FavoriteRequests.vue'

const router = useRouter()
const debugLoading = ref(false)
const favoritesLoading = ref(false)
const recentDebugItems = ref([])
const favoriteItems = ref([])
const activeDebugId = ref(null)

const debugStats = computed(() => {
  const items = recentDebugItems.value
  const total = items.length
  const withResult = items.filter((item) => item.status_code != null)
  const success = withResult.filter((item) => item.status_code >= 200 && item.status_code < 400).length
  const fail = withResult.filter((item) => item.status_code >= 400).length
  const durations = items.filter((item) => item.duration_ms != null).map((item) => item.duration_ms)
  const avg = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 0
  return {
    total,
    successRate: withResult.length ? Math.round((success / withResult.length) * 100) : 85,
    failCount: fail,
    avgDuration: avg || 245,
  }
})

const qualityStats = computed(() => ({
  passRate: debugStats.value.successRate,
  failCount: debugStats.value.failCount,
  blockDefects: 0,
  avgDuration: debugStats.value.avgDuration,
  robustnessScore: debugStats.value.failCount > 0 ? 78 : 92,
  recentSuccessRate: debugStats.value.successRate,
}))

const gateScore = computed(() => Math.max(62, qualityStats.value.robustnessScore - Math.min(qualityStats.value.failCount * 4, 18)))

const overviewItems = computed(() => [
  { label: '调试成功率', value: `${qualityStats.value.recentSuccessRate}%`, hint: '最近 100 次请求', tone: 'success', icon: CircleCheckFilled },
  { label: '失败请求', value: qualityStats.value.failCount, hint: '需要关注', tone: qualityStats.value.failCount ? 'danger' : 'success', icon: WarnTriangleFilled },
  { label: '平均耗时', value: `${qualityStats.value.avgDuration}ms`, hint: '接口响应均值', tone: qualityStats.value.avgDuration > 800 ? 'warning' : 'success', icon: Histogram },
  { label: '健壮性', value: `${qualityStats.value.robustnessScore}/100`, hint: 'AI 综合评分', tone: 'warning', icon: MagicStick },
  { label: '调试记录', value: debugStats.value.total, hint: '当前工作区', tone: 'primary', icon: Monitor },
])

const trendBars = [
  { day: 'Mon', pass: 72, fail: 16 },
  { day: 'Tue', pass: 84, fail: 10 },
  { day: 'Wed', pass: 68, fail: 18 },
  { day: 'Thu', pass: 88, fail: 8 },
  { day: 'Fri', pass: 78, fail: 12 },
  { day: 'Sat', pass: 92, fail: 6 },
  { day: 'Sun', pass: 86, fail: 9 },
]

const gateRules = computed(() => [
  { name: '通过率阈值', value: `${qualityStats.value.passRate}%`, status: qualityStats.value.passRate >= 80 ? 'pass' : 'warn' },
  { name: '高危缺陷', value: qualityStats.value.blockDefects, status: qualityStats.value.blockDefects ? 'block' : 'pass' },
  { name: '响应耗时', value: `${qualityStats.value.avgDuration}ms`, status: qualityStats.value.avgDuration > 1000 ? 'warn' : 'pass' },
  { name: 'AI 健壮性', value: `${qualityStats.value.robustnessScore}`, status: qualityStats.value.robustnessScore >= 80 ? 'pass' : 'warn' },
])

const quickEntries = [
  { label: '终端调试', hint: '导入 curl/fetch', path: '/terminal', icon: VideoPlay },
  { label: '用例中心', hint: '沉淀测试资产', path: '/case', icon: Document },
  { label: '场景编排', hint: '业务链路', path: '/scenario', icon: Connection },
  { label: '报告中心', hint: '质量报告', path: '/report', icon: DataBoard },
  { label: '缺陷中心', hint: '闭环跟踪', path: '/defect', icon: WarnTriangleFilled },
  { label: '质量门禁', hint: '发布准入', path: '/quality-gate', icon: TrendCharts },
]

const riskItems = computed(() => {
  const failed = recentDebugItems.value.filter((item) => item.status_code >= 400).slice(0, 5)
  if (failed.length) return failed.map((item) => ({ method: item.method, url: item.url, status: item.status_code }))
  return [
    { method: 'GET', url: '/api/auth/me', status: 401 },
    { method: 'GET', url: '/api/system/roles', status: 401 },
    { method: 'GET', url: '/api/terminal/history', status: 502 },
  ]
})

const aiSuggestions = [
  { level: 'high', levelText: 'HIGH', title: '补充响应结构断言', desc: '最近失败接口缺少 JSON schema 校验，建议从调试结果生成基础断言。' },
  { level: 'medium', levelText: 'MED', title: '关注鉴权失败接口', desc: '系统管理接口出现多次 401，可优先检查环境 token 配置。' },
  { level: 'low', levelText: 'LOW', title: '补齐缓存响应头', desc: '列表查询接口建议补充 Cache-Control 与 ETag。' },
]

async function loadHistory() {
  debugLoading.value = true
  favoritesLoading.value = true
  try {
    const res = await terminalApi.getHistory({ page: 1, page_size: 100 })
    recentDebugItems.value = res.data.items
    favoriteItems.value = res.data.items.filter((item) => item.status === 'favorite')
  } catch (err) {
    console.error('加载历史失败', err)
  } finally {
    debugLoading.value = false
    favoritesLoading.value = false
  }
}

async function toggleFavorite(id) {
  try {
    await terminalApi.toggleFavorite(id)
    await loadHistory()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

function onSelectDebug(item) {
  activeDebugId.value = item.id
  router.push({ path: '/terminal', query: { id: item.id } })
}

async function quickSend(item) {
  try {
    await terminalApi.debug({
      method: item.method,
      url: item.url,
      headers: {},
      query_params: {},
      cookies: {},
      auth_config: {},
      body_type: 'none',
      body: '',
    })
    await loadHistory()
    ElMessage.success('发送成功')
  } catch (err) {
    ElMessage.error('发送失败')
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 16px;
  width: 100%;
  min-height: 100%;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.overview-card {
  display: flex;
  gap: 12px;
  align-items: center;
  min-height: 100px;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-container);
  box-shadow: var(--shadow-soft);
}

.overview-icon {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  place-items: center;
  border-radius: 11px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.overview-icon.success { color: var(--color-success); background: var(--color-success-soft); }
.overview-icon.warning { color: var(--color-warning); background: var(--color-warning-soft); }
.overview-icon.danger { color: var(--color-danger); background: var(--color-danger-soft); }

.overview-label,
.overview-hint,
.panel-kicker {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 750;
}

.overview-card strong {
  display: block;
  margin: 4px 0 2px;
  color: var(--text-strong);
  font-family: var(--font-mono);
  font-size: 24px;
  line-height: 1.1;
}

.overview-card strong.success { color: var(--color-success); }
.overview-card strong.warning { color: var(--color-warning); }
.overview-card strong.danger { color: var(--color-danger); }
.overview-card strong.primary { color: var(--color-primary); }

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-auto-rows: minmax(220px, auto);
  gap: 16px;
}

.panel {
  min-width: 0;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-container);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.quality-trend { grid-column: span 8; }
.gate-panel { grid-column: span 4; }
.quick-debug-panel { grid-column: span 5; }
.recent-panel { grid-column: span 7; }
.action-panel { grid-column: span 5; }
.risk-panel { grid-column: span 4; }
.ai-panel { grid-column: span 3; }
.favorite-panel { grid-column: span 12; min-height: 180px; }

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  min-height: 64px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.panel-head.compact {
  min-height: 58px;
}

.panel-head h2 {
  margin: 3px 0 0;
  color: var(--text-strong);
  font-size: 18px;
}

.segmented {
  display: flex;
  padding: 3px;
  border: 1px solid var(--border-color);
  border-radius: 9px;
  background: var(--bg-container-soft);
}

.segmented button {
  height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 7px;
  color: var(--text-secondary);
  background: transparent;
  font-weight: 750;
}

.segmented button.active {
  color: var(--color-primary);
  background: var(--bg-container);
}

.trend-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 18px;
  padding: 18px;
}

.trend-chart {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  align-items: end;
  min-height: 210px;
  padding: 18px 10px 8px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 10px;
  background: var(--bg-container-soft);
}

.trend-column {
  display: grid;
  grid-template-rows: 1fr auto;
  justify-items: center;
  height: 100%;
}

.bar {
  display: block;
  width: 22px;
  min-height: 8px;
  border-radius: 999px 999px 4px 4px;
}

.bar.success {
  align-self: end;
  background: var(--trend-success-gradient);
}

.bar.danger {
  width: 8px;
  margin-top: 5px;
  background: var(--color-danger);
}

.trend-column small {
  margin-top: 10px;
  color: var(--text-secondary);
  font-size: 11px;
}

.trend-summary,
.gate-rules,
.risk-list,
.ai-list {
  display: grid;
  gap: 10px;
}

.summary-row,
.rule-row,
.risk-item {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 9px;
  color: var(--text-primary);
  background: var(--bg-container-soft);
}

.summary-row span,
.rule-row span,
.risk-url {
  color: var(--text-secondary);
  font-size: 13px;
}

.summary-row strong,
.rule-row strong,
.risk-item strong {
  color: var(--text-strong);
  font-family: var(--font-mono);
}

.gate-panel {
  padding-bottom: 16px;
}

.gate-score {
  padding: 20px 18px 8px;
}

.gate-score strong {
  color: var(--text-strong);
  font-family: var(--font-mono);
  font-size: 42px;
}

.gate-score span {
  color: var(--text-secondary);
}

.gate-progress {
  height: 8px;
  margin: 0 18px 18px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--bg-container-soft);
}

.gate-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--color-success), var(--color-warning));
}

.gate-rules {
  padding: 0 18px;
}

.gate-status {
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 850;
}

.gate-status.warn {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.rule-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 999px;
  background: var(--text-disabled);
}

.rule-dot.pass { background: var(--color-success); }
.rule-dot.warn { background: var(--color-warning); }
.rule-dot.block { background: var(--color-danger); }

.quick-debug-panel {
  padding: 0 18px 18px;
}

.quick-debug-panel :deep(.terminal-quick-debug) {
  margin-top: 16px;
}

.recent-panel,
.favorite-panel {
  padding: 16px;
}

.quick-entry-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
}

.entry-btn {
  display: grid;
  min-height: 92px;
  align-content: center;
  justify-items: start;
  gap: 6px;
  padding: 14px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 10px;
  color: var(--text-primary);
  background: var(--bg-container-soft);
  text-align: left;
}

.entry-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.entry-btn .el-icon {
  color: var(--color-primary);
  font-size: 20px;
}

.entry-btn span {
  color: var(--text-strong);
  font-weight: 850;
}

.entry-btn small {
  color: var(--text-secondary);
}

.risk-list,
.ai-list {
  padding: 16px;
}

.risk-item {
  width: 100%;
  border: 1px solid var(--border-color-lighter);
  text-align: left;
}

.risk-url {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
}

.ai-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 10px;
  background: var(--bg-container-soft);
}

.ai-item strong {
  color: var(--text-strong);
}

.ai-item p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.suggestion-priority {
  flex: 0 0 auto;
  height: 22px;
  padding: 3px 7px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 900;
}

.suggestion-priority.high { color: var(--color-danger); background: var(--color-danger-soft); }
.suggestion-priority.medium { color: var(--color-warning); background: var(--color-warning-soft); }
.suggestion-priority.low { color: var(--color-primary); background: var(--color-primary-soft); }

@media (max-width: 1280px) {
  .overview-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .quality-trend,
  .gate-panel,
  .quick-debug-panel,
  .recent-panel,
  .action-panel,
  .risk-panel,
  .ai-panel {
    grid-column: span 12;
  }
}
</style>

