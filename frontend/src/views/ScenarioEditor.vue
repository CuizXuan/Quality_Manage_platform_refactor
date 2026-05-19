<template>

  <div class="scenario-editor">

    <div class="toolbar">

      <h2 class="page-title">

        <span class="prompt">&gt;</span> 场景编排

      </h2>

      <button class="btn primary" @click="showModal = true; editing = null; form = defaultForm()">

        <span>+</span> 新建场景

      </button>

    </div>



    <div v-if="scenarioStore.loading" class="loading">

      <span class="loading-spinner">⟳</span>

      加载中...

    </div>

    <div v-else-if="scenarioStore.scenarios.length === 0" class="empty">

      <span class="glitch">// 暂无场景</span>

    </div>

    <div v-else class="scenario-list">

      <div v-for="s in scenarioStore.scenarios" :key="s.id" class="scenario-card panel">

        <div class="scenario-header">

          <div class="scenario-name">

            <span class="scenario-icon">⚙</span>

            {{ s.name }}

          </div>

          <div class="scenario-actions">

            <button class="icon-btn" title="执行" @click="runScenario(s)">▶</button>

            <button class="icon-btn" @click="openScenarioEditor(s)">✏️</button>

            <button class="icon-btn danger" @click="removeScenario(s.id)">🗑</button>

          </div>

        </div>

        <div v-if="s.description" class="scenario-desc">{{ s.description }}</div>

        <div class="step-count">步骤数: {{ s.steps?.length || 0 }}</div>

        

        <!-- 变量预览 -->

        <div v-if="s.variables && Object.keys(s.variables).length > 0" class="scenario-vars">

          <span v-for="(val, key) in s.variables" :key="key" class="var-tag">

            {{ key }}

          </span>

        </div>

      </div>

    </div>



    <!-- 场景详情/编辑弹窗 -->

    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetailModal">

      <div class="modal very-wide">

        <div class="modal-header">

          <h3>// 场景: {{ editingScenario?.name }}</h3>

          <button class="btn-close" @click="closeDetailModal">×</button>

        </div>

        

        <div class="modal-body">

          <!-- 左侧：场景信息 -->

          <div class="scenario-info">

            <div class="form-group">

              <label>场景名称</label>

              <input v-model="editingForm.name" placeholder="场景名称" />

            </div>

            <div class="form-group">

              <label>描述</label>

              <textarea v-model="editingForm.description" rows="2"></textarea>

            </div>

            <div class="form-group">

              <label>初始化变量</label>

              <VariableEditor

                :modelValue="editingForm.variables"

                @update:modelValue="val => editingForm.variables = val"

              />

            </div>

          </div>



          <!-- 右侧：步骤配置 -->

          <div class="steps-panel">

            <div class="steps-header">

              <span>// 步骤列表</span>

              <button class="btn" @click="showAddStepModal = true">+ 添加步骤</button>

            </div>

            

            <div class="steps-list">

              <div v-if="!editingForm.steps?.length" class="empty-steps">

                -- 暂无步骤 --

              </div>

              

              <div

                v-for="(step, i) in editingForm.steps"

                :key="step.id"

                class="step-item"

                :class="{ disabled: !step.enabled }"

                @click="editStep(step)"

              >

                <div class="step-num">{{ i + 1 }}</div>

                <div class="step-info">

                  <div class="step-case">

                    <span class="method-badge" :class="'method-' + (getCaseMethod(step.case_id) || 'get').toLowerCase()">

                      {{ getCaseMethod(step.case_id) || '?' }}

                    </span>

                    <span class="case-name">{{ getCaseName(step.case_id) || `Case #${step.case_id}` }}</span>

                  </div>

                  <div class="step-extracts" v-if="step.extract_rules?.length">

                    <span v-for="rule in step.extract_rules.filter(r => r.enabled)" :key="rule.id" class="extract-tag">

                      {{ rule.name }}

                    </span>

                  </div>

                </div>

                <div class="step-toggle">

                  <input type="checkbox" :checked="step.enabled" @click.stop @change="toggleStep(step)" />

                </div>

                <div class="step-actions">

                  <button class="icon-btn danger" @click.stop="removeStep(i)">×</button>

                </div>

              </div>

            </div>

          </div>

        </div>



        <div class="modal-footer">

          <button class="btn" @click="closeDetailModal">取消</button>

          <button class="btn primary" @click="saveScenarioDetail">保存</button>

        </div>

      </div>

    </div>



    <!-- 添加步骤弹窗 -->

    <div v-if="showAddStepModal" class="modal-overlay" @click.self="showAddStepModal = false">

      <div class="modal">

        <div class="modal-header">

          <h3>// 添加步骤</h3>

          <button class="btn-close" @click="showAddStepModal = false">×</button>

        </div>

        <div class="form-body">

          <div class="form-group">

            <label>选择用例</label>

            <select v-model="newStep.case_id">

              <option value="">-- 请选择 --</option>

              <option v-for="c in availableCases" :key="c.id" :value="c.id">

                {{ c.method }} {{ c.name || c.url }}

              </option>

            </select>

          </div>

          

          <div class="form-group checkbox-group">

            <label>

              <input type="checkbox" v-model="newStep.skip_on_failure" />

              失败时跳过

            </label>

          </div>

          

          <div class="form-group">

            <label>重试次数</label>

            <input type="number" v-model.number="newStep.retry_times" min="0" max="10" />

          </div>



          <!-- 变量提取规则 -->

          <div class="extract-section">

            <div class="extract-header">

              <span>// 变量提取</span>

              <button class="btn-small" @click="addExtractRule">+ 添加</button>

            </div>

            

            <div v-for="(rule, i) in newStep.extract_rules" :key="i" class="extract-rule">

              <input v-model="rule.name" placeholder="变量名" class="rule-name" />

              <select v-model="rule.source">

                <option value="response_body">响应体</option>

                <option value="response_header">响应头</option>

                <option value="response_cookie">Cookie</option>

                <option value="regex">正则</option>

              </select>

              <input v-model="rule.path" placeholder="路径/正则表达式" class="rule-path" />

              <button class="icon-btn danger" @click="removeExtractRule(i)">×</button>

            </div>

          </div>

        </div>

        <div class="form-actions">

          <button class="btn" @click="showAddStepModal = false">取消</button>

          <button class="btn primary" @click="confirmAddStep">添加</button>

        </div>

      </div>

    </div>



    <!-- 新建场景弹窗 -->

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">

      <div class="modal">

        <div class="modal-header">

          <h3>{{ editing ? '// 编辑场景' : '// 新建场景' }}</h3>

          <button class="btn-close" @click="showModal = false">×</button>

        </div>

        <div class="form-body">

          <div class="form-group">

            <label>场景名称</label>

            <input v-model="form.name" placeholder="场景名称" />

          </div>

          <div class="form-group">

            <label>描述</label>

            <textarea v-model="form.description" rows="2"></textarea>

          </div>

        </div>

        <div class="form-actions">

          <button class="btn" @click="showModal = false">取消</button>

          <button class="btn primary" @click="saveScenario">{{ editing ? '保存' : '创建' }}</button>

        </div>

      </div>

    </div>

  </div>

</template>



<script setup>

import { ref, computed, onMounted } from 'vue'

import { useScenarioStore } from '../stores/scenarioStore'

import { useCaseStore } from '../stores/caseStore'

import VariableEditor from '../components/common/VariableEditor.vue'



const scenarioStore = useScenarioStore()

const caseStore = useCaseStore()



const showModal = ref(false)

const showDetailModal = ref(false)

const showAddStepModal = ref(false)

const editing = ref(null)

const editingScenario = ref(null)

const form = ref(defaultForm())

const editingForm = ref({ name: '', description: '', variables: {}, steps: [] })



const newStep = ref({

  case_id: '',

  skip_on_failure: false,

  retry_times: 0,

  enabled: true,

  extract_rules: [],

})



const availableCases = computed(() => caseStore.cases)



function defaultForm() {

  return { name: '', description: '', folder_path: '/', variables: {} }

}



function generateId() {

  return `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

}



function generateExtractId() {

  return `extract_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

}



async function saveScenario() {

  if (!form.value.name) return

  if (editing.value) {

    await scenarioStore.updateScenario(editing.value.id, form.value)

  } else {

    await scenarioStore.createScenario(form.value)

  }

  showModal.value = false

}



function openScenarioEditor(s) {

  editingScenario.value = s

  editingForm.value = {

    name: s.name,

    description: s.description || '',

    variables: { ...s.variables } || {},

    steps: s.steps ? s.steps.map(st => ({ ...st })) : [],

  }

  showDetailModal.value = true

}



function closeDetailModal() {

  showDetailModal.value = false

  editingScenario.value = null

}



async function saveScenarioDetail() {

  if (!editingForm.value.name) return

  await scenarioStore.updateScenario(editingScenario.value.id, {

    name: editingForm.value.name,

    description: editingForm.value.description,

    variables: editingForm.value.variables,

  })

  await scenarioStore.fetchScenarios()

  closeDetailModal()

}



async function runScenario(s) {

  const result = await scenarioStore.runScenario(s.id)

  console.log('场景执行结果', result)

  alert(`执行完成: ${result.status || 'success'}`)

}



async function removeScenario(id) {

  if (!confirm('确认删除？')) return

  await scenarioStore.deleteScenario(id)

}



function getCaseMethod(caseId) {

  const c = availableCases.value.find(c => c.id === caseId)

  return c?.method

}



function getCaseName(caseId) {

  const c = availableCases.value.find(c => c.id === caseId)

  return c?.name || c?.url

}



function addExtractRule() {

  newStep.value.extract_rules.push({

    id: generateExtractId(),

    name: '',

    source: 'response_body',

    path: '$.',

    scope: 'scenario',

    enabled: true,

  })

}



function removeExtractRule(i) {

  newStep.value.extract_rules.splice(i, 1)

}



function confirmAddStep() {

  if (!newStep.value.case_id) {

    alert('请选择用例')

    return

  }

  

  const step = {

    id: generateId(),

    case_id: parseInt(newStep.value.case_id),

    skip_on_failure: newStep.value.skip_on_failure,

    retry_times: newStep.value.retry_times,

    enabled: true,

    extract_rules: newStep.value.extract_rules.filter(r => r.name && r.path),

  }

  

  editingForm.value.steps.push(step)

  scenarioStore.addStep(editingScenario.value.id, step)

  

  newStep.value = {

    case_id: '',

    skip_on_failure: false,

    retry_times: 0,

    enabled: true,

    extract_rules: [],

  }

  showAddStepModal.value = false

}



function editStep(step) {

  editingStep.value = { ...step }

  showStepEditModal.value = true

}



function toggleStep(step) {

  step.enabled = !step.enabled

}



function removeStep(index) {

  const step = editingForm.value.steps[index]

  scenarioStore.deleteStep(editingScenario.value.id, step.id)

  editingForm.value.steps.splice(index, 1)

}



onMounted(() => {

  scenarioStore.fetchScenarios()

  caseStore.fetchCases()

})

</script>



<style scoped>

.scenario-editor {

  padding: 16px;

}



.toolbar {

  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-bottom: 24px;

}



.page-title {

  font-family: var(--font-title);

  font-size: 16px;

  font-weight: 700;

  letter-spacing: 3px;

  color: var(--neon-cyan);

  margin: 0;

  text-shadow: 0 0 10px var(--neon-cyan);

}



.prompt {

  color: var(--neon-magenta);

}



.loading, .empty {

  padding: 40px;

  text-align: center;

  color: var(--text-secondary);

  font-family: var(--font-mono);

}



.loading-spinner {

  display: inline-block;

  animation: spin 1s linear infinite;

  margin-right: 10px;

  color: var(--neon-cyan);

}



.glitch {

  animation: glitch 0.5s infinite;

}



.scenario-list {

  display: grid;

  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));

  gap: 16px;

}



.scenario-card {

  padding: 16px;

  transition: all var(--transition-fast);

}



.scenario-card:hover {

  border-color: var(--neon-cyan);

  box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);

}



.scenario-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-bottom: 8px;

}



.scenario-name {

  font-family: var(--font-title);

  font-size: 14px;

  font-weight: 600;

  letter-spacing: 1px;

  color: var(--neon-cyan);

  display: flex;

  align-items: center;

  gap: 8px;

}



.scenario-icon {

  color: var(--neon-magenta);

}



.scenario-desc {

  font-size: 12px;

  color: var(--text-secondary);

  margin-bottom: 8px;

}



.step-count {

  font-family: var(--font-mono);

  font-size: 11px;

  color: var(--text-secondary);

  letter-spacing: 1px;

}



.scenario-vars {

  display: flex;

  flex-wrap: wrap;

  gap: 4px;

  margin-top: 8px;

}



.var-tag {

  font-family: var(--font-mono);

  font-size: 10px;

  background: rgba(0, 255, 255, 0.1);

  padding: 2px 6px;

  border-radius: 2px;

  color: var(--neon-cyan);

}



.scenario-actions {

  display: flex;

  gap: 4px;

}



.icon-btn {

  background: transparent;

  border: 1px solid var(--border-default);

  cursor: pointer;

  padding: 4px 8px;

  font-size: 12px;

  color: var(--text-secondary);

  transition: all var(--transition-fast);

}



.icon-btn:hover {

  border-color: var(--neon-cyan);

  color: var(--neon-cyan);

}



.icon-btn.danger:hover {

  border-color: var(--neon-pink);

  color: var(--neon-pink);

}



.modal-overlay {

  position: fixed;

  inset: 0;

  background: rgba(0, 0, 0, 0.85);

  backdrop-filter: blur(4px);

  display: flex;

  align-items: center;

  justify-content: center;

  z-index: 100;

}



.modal {

  background: var(--bg-panel);

  border: 1px solid var(--neon-cyan);

  box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);

  width: 480px;

  max-height: 80vh;

  overflow-y: auto;

}

/* 禁用 panel 角落装饰 */
.modal::before,
.modal::after {
  display: none;
}




.modal.very-wide {

  width: 900px;

}



.modal-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  padding: 16px 20px;

  border-bottom: 1px solid var(--border-default);

}



.modal-header h3 {

  font-family: var(--font-title);

  font-size: 14px;

  font-weight: 600;

  letter-spacing: 2px;

  color: var(--neon-cyan);

  margin: 0;

}



.btn-close {

  background: none;

  border: none;

  font-size: 20px;

  color: var(--text-secondary);

  cursor: pointer;

}



.modal-body {

  display: grid;

  grid-template-columns: 1fr 1fr;

  gap: 20px;

  padding: 20px;

}



.scenario-info, .steps-panel {

  display: flex;

  flex-direction: column;

  gap: 12px;

}



.steps-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  font-family: var(--font-title);

  font-size: 11px;

  letter-spacing: 2px;

  color: var(--neon-magenta);

  margin-bottom: 8px;

}



.steps-list {

  border: 1px solid var(--border-default);

  border-radius: 4px;

  overflow: hidden;

  max-height: 350px;

  overflow-y: auto;

}



.step-item {

  display: flex;

  align-items: center;

  gap: 10px;

  padding: 10px 12px;

  border-bottom: 1px solid var(--border-default);

  cursor: pointer;

  transition: all var(--transition-fast);

}



.step-item:last-child {

  border-bottom: none;

}



.step-item.disabled {

  opacity: 0.5;

}



.step-item:hover {

  background: rgba(0, 255, 255, 0.05);

}



.step-num {

  width: 24px;

  height: 24px;

  border-radius: 50%;

  background: var(--neon-cyan);

  color: var(--bg-primary);

  display: flex;

  align-items: center;

  justify-content: center;

  font-family: var(--font-title);

  font-size: 11px;

  font-weight: 700;

  flex-shrink: 0;

}



.step-info {

  flex: 1;

  min-width: 0;

}



.step-case {

  display: flex;

  align-items: center;

  gap: 6px;

  font-size: 12px;

}



.case-name {

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

}



.step-extracts {

  display: flex;

  flex-wrap: wrap;

  gap: 4px;

  margin-top: 4px;

}



.extract-tag {

  font-family: var(--font-mono);

  font-size: 10px;

  background: rgba(0, 255, 255, 0.1);

  padding: 1px 4px;

  border-radius: 2px;

  color: var(--neon-magenta);

}



.step-toggle input {

  width: 16px;

  height: 16px;

  cursor: pointer;

}



.step-actions {

  flex-shrink: 0;

}



.empty-steps {

  padding: 20px;

  text-align: center;

  color: var(--text-secondary);

  font-family: var(--font-mono);

  font-size: 12px;

}



.modal-footer {

  display: flex;

  gap: 12px;

  justify-content: flex-end;

  padding: 16px 20px;

  border-top: 1px solid var(--border-default);

}



.form-body {

  padding: 20px;

}



.form-group {

  margin-bottom: 16px;

}



.form-group label {

  display: block;

  font-family: var(--font-title);

  font-size: 10px;

  letter-spacing: 1px;

  color: var(--text-secondary);

  margin-bottom: 6px;

}



.form-group input,

.form-group textarea,

.form-group select {

  width: 100%;

  padding: 10px 12px;

  background: var(--bg-secondary);

  border: 1px solid var(--border-default);

  color: var(--neon-cyan);

  font-family: var(--font-mono);

  font-size: 12px;

  outline: none;

  box-sizing: border-box;

}



.form-group input:focus,

.form-group textarea:focus,

.form-group select:focus {

  border-color: var(--neon-cyan);

  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);

}



.checkbox-group label {

  display: flex;

  align-items: center;

  gap: 8px;

  cursor: pointer;

  color: var(--neon-cyan);

  font-family: var(--font-title);

  font-size: 11px;

  letter-spacing: 1px;

}



.extract-section {

  background: var(--bg-secondary);

  border-radius: 4px;

  padding: 12px;

  margin-top: 8px;

}



.extract-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-bottom: 8px;

  font-family: var(--font-title);

  font-size: 10px;

  letter-spacing: 1px;

  color: var(--text-secondary);

}



.extract-rule {

  display: flex;

  gap: 6px;

  margin-bottom: 8px;

  align-items: center;

}



.rule-name {

  width: 90px;

  padding: 6px;

}



.rule-path {

  flex: 1;

  padding: 6px;

}



.extract-rule select {

  width: 90px;

  padding: 6px;

}



.form-actions {

  display: flex;

  gap: 12px;

  justify-content: flex-end;

  padding: 16px 20px;

  border-top: 1px solid var(--border-default);

}



@keyframes spin {

  from { transform: rotate(0deg); }

  to { transform: rotate(360deg); }

}



@keyframes glitch {

  0% { transform: translate(0); opacity: 0.7; }

  20% { transform: translate(-2px, 2px); opacity: 0.8; }

  40% { transform: translate(-2px, -2px); opacity: 0.7; }

  60% { transform: translate(2px, 2px); opacity: 0.8; }

  80% { transform: translate(2px, -2px); opacity: 0.7; }

  100% { transform: translate(0); opacity: 0.7; }

}

</style>

