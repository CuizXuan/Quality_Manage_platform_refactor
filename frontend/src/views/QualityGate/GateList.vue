<template>
  <div class="gate-list">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 质量门禁
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建门禁
      </button>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="gates.length === 0" class="empty">
      <span class="glitch">// 暂无质量门禁</span>
    </div>
    <div v-else class="gate-grid">
      <div
        v-for="gate in gates"
        :key="gate.id"
        class="gate-card panel"
        @click="openGateEditor(gate)"
      >
        <div class="gate-header">
          <span class="gate-icon">⚖</span>
          <span class="gate-name">{{ gate.name }}</span>
          <span class="gate-toggle" :class="{ enabled: gate.enabled }" @click.stop="toggleGate(gate)">
            {{ gate.enabled ? '◉' : '○' }}
          </span>
        </div>
        <div class="gate-desc">{{ gate.description || '暂无描述' }}</div>
        <div class="gate-stats">
          <div class="gate-stat">
            <span class="gs-label">规则</span>
            <span class="gs-value">{{ (gate.rules || []).length }}</span>
          </div>
          <div class="gate-stat">
            <span class="gs-label">最近评估</span>
            <span class="gs-value" :class="lastResultClass(gate.id)">{{ lastResultLabel(gate.id) }}</span>
          </div>
        </div>
        <div class="gate-footer">
          <button class="btn" @click.stop="evaluateGate(gate)">⚡ 评估</button>
          <button class="icon-btn" @click.stop="openEditModal(gate)">✏️</button>
          <button class="icon-btn danger" @click.stop="deleteGate(gate.id)">🗑</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editing ? '// 编辑门禁' : '// 新建门禁' }}</h3>
          <button class="btn-close" @click="showModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>名称 *</label>
            <input v-model="form.name" placeholder="门禁名称" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description" rows="2" placeholder="描述..."></textarea>
          </div>
          <div class="form-group">
            <label>启用状态</label>
            <label class="switch-label">
              <input type="checkbox" v-model="form.enabled" />
              <span>{{ form.enabled ? '启用' : '禁用' }}</span>
            </label>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showModal = false">取消</button>
          <button class="btn primary" @click="saveGate" :disabled="saving || !form.name">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Gate Editor Modal -->
    <div v-if="showEditor" class="modal-overlay" @click.self="showEditor = false">
      <div class="modal editor-modal">
        <div class="modal-header">
          <h3>// {{ editorGate?.name || '门禁编辑器' }}</h3>
          <button class="btn-close" @click="showEditor = false">×</button>
        </div>
        <div class="editor-body" v-if="editorGate">
          <div class="editor-info">
            <div class="form-group">
              <label>描述</label>
              <input v-model="editorGate.description" placeholder="描述" />
            </div>
            <div class="form-group">
              <label>启用</label>
              <label class="switch-label">
                <input type="checkbox" v-model="editorGate.enabled" />
                <span>{{ editorGate.enabled ? '启用' : '禁用' }}</span>
              </label>
            </div>
          </div>

          <div class="rules-section">
            <div class="rules-header">
              <label>规则 ({{ (editorGate.rules || []).length }})</label>
              <button class="btn" @click="addRule">+ 添加规则</button>
            </div>
            <div v-if="(editorGate.rules || []).length === 0" class="empty-rules">
              <span class="glitch">// 暂无规则</span>
            </div>
            <div v-for="(rule, idx) in editorGate.rules || []" :key="idx" class="rule-item">
              <div class="rule-fields">
                <div class="rule-field">
                  <label>类型</label>
                  <select v-model="rule.type">
                    <option value="coverage">覆盖率</option>
                    <option value="complexity">复杂度</option>
                    <option value="duplication">重复率</option>
                    <option value="comment">注释率</option>
                  </select>
                </div>
                <div class="rule-field">
                  <label>指标</label>
                  <input v-model="rule.metric" placeholder="e.g. line_coverage" />
                </div>
                <div class="rule-field">
                  <label>操作符</label>
                  <select v-model="rule.operator">
                    <option value="gte">≥</option>
                    <option value="lte">≤</option>
                    <option value="gt">&gt;</option>
                    <option value="lt">&lt;</option>
                    <option value="eq">=</option>
                  </select>
                </div>
                <div class="rule-field">
                  <label>阈值</label>
                  <input v-model.number="rule.threshold" type="number" step="0.01" placeholder="0.8" />
                </div>
                <div class="rule-field">
                  <label>范围</label>
                  <input v-model="rule.scope" placeholder="src/" />
                </div>
              </div>
              <div class="rule-result" v-if="rule.result !== undefined">
                <span :class="rule.result ? 'result-pass' : 'result-fail'">
                  {{ rule.result ? '🟢 通过' : '🔴 失败' }}
                </span>
              </div>
              <button class="icon-btn danger" @click="removeRule(idx)">🗑</button>
            </div>
          </div>

          <div class="editor-actions">
            <button class="btn" @click="showEditor = false">取消</button>
            <button class="btn primary" @click="saveEditorGate" :disabled="saving">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { qualityGateApi } from '../../api/qualityGate'

const gates = ref([])
const loading = ref(true)
const showModal = ref(false)
const showEditor = ref(false)
const editing = ref(null)
const editorGate = ref(null)
const saving = ref(false)
const form = ref(defaultForm())
const evalResults = ref({})

function defaultForm() {
  return { name: '', description: '', enabled: true, rules: [] }
}

async function fetchGates() {
  loading.value = true
  try {
    const res = await qualityGateApi.list()
    gates.value = res.data.data || []
  } catch {
    gates.value = []
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  showModal.value = true
}

function openEditModal(gate) {
  editing.value = gate
  form.value = { name: gate.name, description: gate.description, enabled: gate.enabled, rules: gate.rules || [] }
  showModal.value = true
}

function openGateEditor(gate) {
  editorGate.value = JSON.parse(JSON.stringify(gate))
  showEditor.value = true
}

async function saveGate() {
  if (!form.value.name) return
  saving.value = true
  try {
    if (editing.value) {
      await qualityGateApi.update(editing.value.id, form.value)
    } else {
      await qualityGateApi.create(form.value)
    }
    showModal.value = false
    await fetchGates()
  } finally {
    saving.value = false
  }
}

async function saveEditorGate() {
  if (!editorGate.value) return
  saving.value = true
  try {
    await qualityGateApi.update(editorGate.value.id, {
      name: editorGate.value.name,
      description: editorGate.value.description,
      enabled: editorGate.value.enabled,
      rules: editorGate.value.rules || [],
    })
    showEditor.value = false
    await fetchGates()
  } finally {
    saving.value = false
  }
}

async function toggleGate(gate) {
  await qualityGateApi.update(gate.id, { enabled: !gate.enabled })
  await fetchGates()
}

async function evaluateGate(gate) {
  try {
    const res = await qualityGateApi.evaluate(gate.id)
    evalResults.value[gate.id] = res.data
    await fetchGates()
  } catch {}
}

async function deleteGate(id) {
  if (!confirm('确定要删除吗？')) return
  await qualityGateApi.delete(id)
  await fetchGates()
}

function addRule() {
  if (!editorGate.value) return
  if (!editorGate.value.rules) editorGate.value.rules = []
  editorGate.value.rules.push({ type: 'coverage', metric: 'line_coverage', operator: 'gte', threshold: 0.8, scope: '' })
}

function removeRule(idx) {
  if (!editorGate.value?.rules) return
  editorGate.value.rules.splice(idx, 1)
}

function lastResultLabel(id) {
  const r = evalResults.value[id]
  if (!r) return '--'
  return r.passed ? '通过' : '失败'
}

function lastResultClass(id) {
  const r = evalResults.value[id]
  if (!r) return ''
  return r.passed ? 'text-green' : 'text-red'
}

onMounted(() => fetchGates())
</script>

<style scoped>
.gate-list { padding: 16px; }

.toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
}
.page-title {
  font-family: var(--font-title); font-size: 16px; font-weight: 700;
  letter-spacing: 3px; color: var(--neon-cyan); margin: 0; text-shadow: 0 0 10px var(--neon-cyan);
}
.prompt { color: var(--neon-magenta); }

.loading { padding: 40px; text-align: center; color: var(--neon-cyan); }
.loading-spinner { display: inline-block; animation: spin 1s linear infinite; margin-right: 10px; }
.empty { padding: 40px; text-align: center; color: var(--text-secondary); }
.glitch { font-family: var(--font-mono); animation: glitch 0.5s infinite; }

.gate-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;
}

.gate-card {
  padding: 16px; cursor: pointer; transition: all var(--transition-fast);
}
.gate-card:hover { border-color: var(--neon-cyan); box-shadow: 0 0 15px rgba(0,255,255,0.2); }

.gate-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.gate-icon { font-size: 20px; color: var(--neon-magenta); }
.gate-name { font-family: var(--font-title); font-size: 14px; font-weight: 600; letter-spacing: 1px; color: var(--neon-cyan); flex: 1; }
.gate-toggle { font-size: 16px; cursor: pointer; color: var(--text-secondary); transition: all var(--transition-fast); }
.gate-toggle.enabled { color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green); }

.gate-desc { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); margin-bottom: 12px; min-height: 28px; }

.gate-stats { display: flex; gap: 24px; margin-bottom: 12px; }
.gate-stat { display: flex; flex-direction: column; gap: 2px; }
.gs-label { font-family: var(--font-title); font-size: 9px; letter-spacing: 1px; color: var(--text-secondary); text-transform: uppercase; }
.gs-value { font-family: var(--font-mono); font-size: 14px; color: var(--neon-cyan); }
.text-green { color: var(--neon-green); }
.text-red { color: var(--neon-red); }

.gate-footer { display: flex; gap: 8px; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-default); }

.icon-btn {
  background: transparent; border: 1px solid var(--border-default); cursor: pointer;
  padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast);
}
.icon-btn:hover { border-color: var(--neon-cyan); color: var(--neon-cyan); }
.icon-btn.danger:hover { border-color: var(--neon-pink); color: var(--neon-pink); }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: var(--bg-panel); border: 1px solid var(--neon-cyan);
  box-shadow: 0 0 30px rgba(0,255,255,0.3);
}
.modal::before, .modal::after { display: none; }
.editor-modal { width: 800px; max-height: 85vh; overflow-y: auto; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-default);
}
.modal-header h3 {
  font-family: var(--font-title); font-size: 14px; font-weight: 600; letter-spacing: 2px;
  color: var(--neon-cyan); margin: 0;
}
.btn-close { background: none; border: none; font-size: 20px; color: var(--text-secondary); cursor: pointer; }
.form-body { padding: 20px; }
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  color: var(--text-secondary); margin-bottom: 6px; text-transform: uppercase;
}
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
.switch-label {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  color: var(--neon-cyan); font-family: var(--font-title); font-size: 11px; letter-spacing: 1px;
}
.form-actions {
  display: flex; gap: 12px; justify-content: flex-end;
  padding: 16px 20px; border-top: 1px solid var(--border-default);
}

.editor-body { padding: 20px; }
.editor-info { display: flex; gap: 16px; align-items: flex-end; margin-bottom: 24px; }
.editor-info .form-group { flex: 1; margin-bottom: 0; }

.rules-section { margin-bottom: 24px; }
.rules-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rules-header label {
  font-family: var(--font-title); font-size: 11px; letter-spacing: 2px; color: var(--neon-cyan); text-transform: uppercase;
}
.empty-rules { padding: 20px; text-align: center; }

.rule-item {
  display: flex; align-items: flex-end; gap: 12px; padding: 12px;
  border: 1px solid var(--border-default); border-radius: 4px; margin-bottom: 8px;
  background: var(--bg-secondary);
}
.rule-fields { display: flex; gap: 8px; flex: 1; flex-wrap: wrap; }
.rule-field { display: flex; flex-direction: column; gap: 4px; min-width: 100px; }
.rule-field label {
  font-family: var(--font-title); font-size: 9px; letter-spacing: 1px; color: var(--text-secondary); text-transform: uppercase;
}
.rule-field input, .rule-field select {
  padding: 6px 8px; background: var(--bg-panel);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 11px; outline: none;
}
.rule-result { padding-bottom: 6px; }
.result-pass { color: var(--neon-green); font-family: var(--font-mono); font-size: 11px; }
.result-fail { color: var(--neon-red); font-family: var(--font-mono); font-size: 11px; }

.editor-actions { display: flex; gap: 12px; justify-content: flex-end; padding-top: 16px; border-top: 1px solid var(--border-default); }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes glitch {
  0% { transform: translate(0); opacity: 0.7; }
  20% { transform: translate(-2px, 2px); opacity: 0.8; }
  40% { transform: translate(-2px, -2px); opacity: 0.7; }
  60% { transform: translate(2px, 2px); opacity: 0.8; }
  80% { transform: translate(2px, -2px); opacity: 0.7; }
  100% { transform: translate(0); opacity: 0.7; }
}
</style>
