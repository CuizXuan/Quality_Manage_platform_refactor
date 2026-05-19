<template>
  <div class="gate-editor">
    <div class="editor-header">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> {{ isNew ? '新建质量门禁' : '编辑质量门禁' }}
      </h2>
      <button class="btn" @click="emit('close')">← 返回</button>
    </div>

    <!-- 基本信息 -->
    <div class="section panel">
      <h3 class="section-title">// 基本信息</h3>
      <div class="form-row">
        <div class="form-group flex-2">
          <label>门禁名称</label>
          <input v-model="form.name" placeholder="生产发布门禁" />
        </div>
        <div class="form-group flex-1">
          <label>启用状态</label>
          <label class="switch-label">
            <input type="checkbox" v-model="form.enabled" />
            <span>{{ form.enabled ? '已启用' : '已禁用' }}</span>
          </label>
        </div>
      </div>
      <div class="form-group">
        <label>描述</label>
        <input v-model="form.description" placeholder="生产环境部署前的质量检查" />
      </div>
    </div>

    <!-- 门禁规则 -->
    <div class="section panel">
      <div class="rules-header">
        <h3 class="section-title">// 门禁规则</h3>
        <button class="btn" @click="addRule">+ 添加规则</button>
      </div>

      <div v-if="form.rules.length === 0" class="empty-rules">
        <span class="glitch">// 暂无规则，点击上方添加</span>
      </div>

      <div v-for="(rule, i) in form.rules" :key="i" class="rule-item">
        <div class="rule-header">
          <span class="rule-num">{{ i + 1 }}</span>
          <span class="rule-type-badge" :class="'type-' + rule.type">{{ ruleTypeText(rule.type) }}</span>
          <button class="icon-btn danger" @click="removeRule(i)">×</button>
        </div>
        <div class="rule-body">
          <div class="rule-field">
            <label>规则类型</label>
            <select v-model="rule.type" @change="onTypeChange(rule)">
              <option value="coverage">覆盖率</option>
              <option value="test_pass_rate">用例通过率</option>
              <option value="response_time">响应时间</option>
              <option value="critical_defects">严重缺陷数</option>
            </select>
          </div>
          <div class="rule-field" v-if="rule.type === 'coverage'">
            <label>指标</label>
            <select v-model="rule.metric">
              <option value="line_coverage">行覆盖率</option>
              <option value="branch_coverage">分支覆盖率</option>
              <option value="function_coverage">函数覆盖率</option>
            </select>
          </div>
          <div class="rule-field">
            <label>条件</label>
            <select v-model="rule.operator">
              <option value="gte">≥ (大于等于)</option>
              <option value="lte">≤ (小于等于)</option>
              <option value="eq">= (等于)</option>
            </select>
          </div>
          <div class="rule-field">
            <label>阈值</label>
            <input type="number" v-model.number="rule.threshold" placeholder="80" />
          </div>
          <div class="rule-field" v-if="rule.type !== 'critical_defects'">
            <label>应用范围</label>
            <select v-model="rule.scope">
              <option value="overall">整体</option>
              <option value="file">指定文件</option>
              <option value="case">指定用例</option>
              <option value="scenario">指定场景</option>
            </select>
          </div>
          <div class="rule-field" v-if="rule.scope === 'file' || rule.scope === 'case' || rule.scope === 'scenario'">
            <label>目标ID</label>
            <input v-model="rule.scope_id" type="number" placeholder="1" />
          </div>
          <div class="rule-field">
            <label>阻断级别</label>
            <select v-model="rule.level">
              <option value="block">阻断</option>
              <option value="warn">警告</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-bar">
      <button class="btn" @click="emit('close')">取消</button>
      <button class="btn primary" @click="saveGate" :disabled="saving">
        {{ saving ? '保存中...' : '保存' }}
      </button>
      <button class="btn" @click="testEvaluate" :disabled="evaluating || isNew">
        {{ evaluating ? '评估中...' : '测试评估' }}
      </button>
    </div>

    <!-- 评估结果 -->
    <div v-if="evalResult" class="eval-result panel">
      <h3 class="section-title">// 评估结果</h3>
      <div class="result-summary">
        <span class="result-status" :class="'result-' + evalResult.status">
          {{ resultStatusText(evalResult.status) }}
        </span>
        <span>{{ evalResult.summary }}</span>
      </div>
      <div class="rule-results">
        <div v-for="r in evalResult.rule_results" :key="r.id" class="rule-result-item" :class="'result-' + r.status">
          <span class="rr-icon">{{ r.status === 'passed' ? '🟢' : r.status === 'warning' ? '🟡' : '🔴' }}</span>
          <span class="rr-name">{{ r.type }} - {{ r.metric || '' }}</span>
          <span class="rr-message">{{ r.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { qualityGateApi } from '../../api/qualityGate'

const props = defineProps({
  gateId: { type: Number, default: null },
})
const emit = defineEmits(['close', 'saved'])

const isNew = computed(() => !props.gateId)
const saving = ref(false)
const evaluating = ref(false)
const evalResult = ref(null)

const defaultRule = () => ({
  id: `rule_${Date.now()}`,
  type: 'coverage',
  metric: 'line_coverage',
  operator: 'gte',
  threshold: 80,
  scope: 'overall',
  scope_id: null,
  level: 'block',
})

const form = ref({
  name: '',
  description: '',
  enabled: true,
  rules: [],
})

function ruleTypeText(type) {
  return { coverage: '覆盖率', test_pass_rate: '用例通过率', response_time: '响应时间', critical_defects: '严重缺陷数' }[type] || type
}
function resultStatusText(s) {
  return { passed: '通过', failed: '失败', warning: '警告' }[s] || s
}

function addRule() {
  form.value.rules.push(defaultRule())
}
function removeRule(i) {
  form.value.rules.splice(i, 1)
}
function onTypeChange(rule) {
  if (rule.type === 'critical_defects') {
    rule.metric = null
    rule.threshold = 0
  }
}

async function loadGate() {
  if (!props.gateId) return
  const res = await qualityGateApi.get(props.gateId)
  const g = res.data
  form.value = {
    name: g.name,
    description: g.description || '',
    enabled: g.enabled,
    rules: JSON.parse(g.rules || '[]'),
  }
}

async function saveGate() {
  if (!form.value.name) return
  saving.value = true
  try {
    const data = { ...form.value }
    if (props.gateId) {
      await qualityGateApi.update(props.gateId, data)
    } else {
      await qualityGateApi.create(data)
    }
    emit('saved')
    emit('close')
  } finally {
    saving.value = false
  }
}

async function testEvaluate() {
  if (!props.gateId) return
  evaluating.value = true
  try {
    const res = await qualityGateApi.evaluate(props.gateId, { trigger_type: 'manual', trigger_ref: '' })
    evalResult.value = res.data
  } finally {
    evaluating.value = false
  }
}

// Initialize
if (props.gateId) loadGate()
else form.value.rules.push(defaultRule())
</script>

<style scoped>
.gate-editor { padding: 16px; max-width: 900px; }
.editor-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title {
  font-family: var(--font-title); font-size: 16px; font-weight: 700;
  letter-spacing: 3px; color: var(--neon-cyan); margin: 0;
}
.prompt { color: var(--neon-magenta); }
.section { padding: 16px; margin-bottom: 16px; }
.section-title {
  font-family: var(--font-title); font-size: 12px; font-weight: 600;
  letter-spacing: 2px; color: var(--neon-cyan); margin: 0 0 12px 0;
}
.rules-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rules-header .section-title { margin: 0; }
.form-row { display: flex; gap: 12px; margin-bottom: 12px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group.flex-2 { flex: 2; }
.form-group.flex-1 { flex: 1; }
.form-group label { font-size: 10px; color: var(--text-secondary); font-family: var(--font-title); letter-spacing: 1px; }
.form-group input[type="text"], .form-group input[type="number"], .form-group select {
  padding: 8px 10px; background: var(--bg-secondary); border: 1px solid var(--border-default);
  color: var(--neon-cyan); font-family: var(--font-mono); font-size: 12px; outline: none;
}
.switch-label { display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--neon-cyan); font-family: var(--font-title); font-size: 11px; }
.empty-rules { padding: 20px; text-align: center; color: var(--text-secondary); font-family: var(--font-mono); font-size: 12px; }
.glitch { animation: glitch 0.5s infinite; }
.rule-item {
  border: 1px solid var(--border-default); padding: 12px; margin-bottom: 10px; border-radius: 4px;
}
.rule-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.rule-num { font-family: var(--font-title); font-size: 11px; color: var(--text-secondary); }
.rule-type-badge { padding: 2px 8px; border-radius: 3px; font-size: 10px; font-family: var(--font-title); font-weight: 600; letter-spacing: 1px; }
.type-coverage { background: rgba(0,255,255,0.15); color: var(--neon-cyan); border: 1px solid var(--neon-cyan); }
.type-test_pass_rate { background: rgba(0,255,0,0.15); color: var(--neon-green); border: 1px solid var(--neon-green); }
.type-response_time { background: rgba(255,165,0,0.15); color: #ffa500; border: 1px solid #ffa500; }
.type-critical_defects { background: rgba(255,0,0,0.15); color: #f00; border: 1px solid #f00; }
.rule-body { display: flex; gap: 10px; flex-wrap: wrap; }
.rule-field { display: flex; flex-direction: column; gap: 4px; min-width: 120px; }
.rule-field label { font-size: 9px; color: var(--text-secondary); font-family: var(--font-title); letter-spacing: 1px; }
.rule-field select, .rule-field input { padding: 6px 8px; background: var(--bg-secondary); border: 1px solid var(--border-default); color: var(--neon-cyan); font-family: var(--font-mono); font-size: 11px; outline: none; }
.actions-bar { display: flex; gap: 10px; margin-bottom: 16px; }
.eval-result { padding: 16px; }
.result-summary { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; font-family: var(--font-title); font-size: 13px; }
.result-status { font-size: 14px; font-weight: 700; }
.result-passed { color: var(--neon-green); }
.result-failed { color: #f00; }
.result-warning { color: #ffa500; }
.rule-results { display: flex; flex-direction: column; gap: 6px; }
.rule-result-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 4px; font-size: 12px; }
.rr-icon { font-size: 14px; }
.rr-name { font-family: var(--font-title); font-size: 11px; color: var(--neon-cyan); min-width: 120px; }
.rr-message { color: var(--text-secondary); font-family: var(--font-mono); font-size: 11px; }
.icon-btn { background: transparent; border: 1px solid var(--border-default); cursor: pointer; padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast); }
.icon-btn.danger:hover { border-color: var(--neon-pink); color: var(--neon-pink); }
@keyframes glitch {
  0% { transform: translate(0); opacity: 0.7; }
  20% { transform: translate(-2px, 2px); opacity: 0.8; }
  40% { transform: translate(-2px, -2px); opacity: 0.7; }
  60% { transform: translate(2px, 2px); opacity: 0.8; }
  80% { transform: translate(2px, -2px); opacity: 0.7; }
  100% { transform: translate(0); opacity: 0.7; }
}
</style>
