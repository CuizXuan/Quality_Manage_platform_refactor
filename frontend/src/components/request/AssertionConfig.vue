<template>
  <div class="assertion-config">
    <div class="assertion-header">
      <span class="title">断言配置</span>
      <button class="btn-add" @click="addAssertion" title="添加断言">+ 添加断言</button>
    </div>

    <!-- 断言列表 -->
    <div v-if="assertions.length === 0" class="empty-assertions">
      <span>暂无断言，点击"添加断言"开始配置</span>
    </div>

    <div v-else class="assertion-list">
      <div
        v-for="(assertion, index) in assertions"
        :key="assertion.id"
        class="assertion-item"
        :class="{ disabled: !assertion.enabled, failed: assertion._failed }"
      >
        <!-- 断言开关 -->
        <div class="assertion-toggle">
          <input
            type="checkbox"
            :checked="assertion.enabled"
            @change="toggleAssertion(index)"
          />
        </div>

        <!-- 断言类型 -->
        <div class="assertion-type">
          <select v-model="assertion.type" @change="onTypeChange(assertion)">
            <option value="status_code">状态码</option>
            <option value="json_path">JSONPath</option>
            <option value="response_time">响应时间</option>
            <option value="header">响应头</option>
            <option value="body_contains">响应体包含</option>
          </select>
        </div>

        <!-- 断言内容 -->
        <div class="assertion-content">
          <!-- 状态码 -->
          <template v-if="assertion.type === 'status_code'">
            <select v-model="assertion.operator">
              <option value="equals">等于</option>
              <option value="not_equals">不等于</option>
            </select>
            <input
              v-model.number="assertion.expected"
              type="number"
              placeholder="200"
              class="short-input"
            />
          </template>

          <!-- JSONPath -->
          <template v-else-if="assertion.type === 'json_path'">
            <input
              v-model="assertion.path"
              placeholder="$.data.token"
              class="path-input"
            />
            <select v-model="assertion.operator">
              <option value="equals">等于</option>
              <option value="not_equals">不等于</option>
              <option value="contains">包含</option>
              <option value="exists">存在</option>
              <option value="not_exists">不存在</option>
              <option value="greater_than">大于</option>
              <option value="less_than">小于</option>
            </select>
            <input
              v-model="assertion.expected"
              placeholder="期望值"
              class="expected-input"
            />
          </template>

          <!-- 响应时间 -->
          <template v-else-if="assertion.type === 'response_time'">
            <select v-model="assertion.operator">
              <option value="less_than">小于</option>
              <option value="greater_than">大于</option>
            </select>
            <input
              v-model.number="assertion.expected"
              type="number"
              placeholder="1000"
              class="short-input"
            />
            <span class="unit">ms</span>
          </template>

          <!-- 响应头 -->
          <template v-else-if="assertion.type === 'header'">
            <input
              v-model="assertion.header_name"
              placeholder="Content-Type"
              class="short-input"
            />
            <select v-model="assertion.operator">
              <option value="equals">等于</option>
              <option value="contains">包含</option>
              <option value="exists">存在</option>
            </select>
            <input
              v-model="assertion.expected"
              placeholder="期望值"
              class="expected-input"
            />
          </template>

          <!-- 响应体包含 -->
          <template v-else-if="assertion.type === 'body_contains'">
            <select v-model="assertion.operator">
              <option value="contains">包含</option>
              <option value="not_contains">不包含</option>
            </select>
            <input
              v-model="assertion.expected"
              placeholder="期望包含的文本"
              class="expected-input full"
            />
          </template>
        </div>

        <!-- 结果显示 -->
        <div v-if="assertion._result !== undefined" class="assertion-result">
          <span v-if="assertion._result.passed" class="result-pass">✅</span>
          <span v-else class="result-fail">❌</span>
        </div>

        <!-- 删除按钮 -->
        <button class="btn-delete" @click="removeAssertion(index)" title="删除">×</button>
      </div>
    </div>

    <!-- 添加断言弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <h3>添加断言</h3>
        <div class="form-group">
          <label>断言类型</label>
          <select v-model="newAssertion.type">
            <option value="status_code">状态码</option>
            <option value="json_path">JSONPath 取值</option>
            <option value="response_time">响应时间</option>
            <option value="header">响应头</option>
            <option value="body_contains">响应体包含</option>
          </select>
        </div>

        <!-- 状态码 -->
        <template v-if="newAssertion.type === 'status_code'">
          <div class="form-group">
            <label>操作符</label>
            <select v-model="newAssertion.operator">
              <option value="equals">等于</option>
              <option value="not_equals">不等于</option>
            </select>
          </div>
          <div class="form-group">
            <label>期望状态码</label>
            <input v-model.number="newAssertion.expected" type="number" placeholder="200" />
          </div>
        </template>

        <!-- JSONPath -->
        <template v-else-if="newAssertion.type === 'json_path'">
          <div class="form-group">
            <label>JSONPath 路径</label>
            <input v-model="newAssertion.path" placeholder="$.code 或 $.data.list[0].name" />
          </div>
          <div class="form-group">
            <label>操作符</label>
            <select v-model="newAssertion.operator">
              <option value="equals">等于</option>
              <option value="not_equals">不等于</option>
              <option value="contains">包含</option>
              <option value="exists">存在</option>
              <option value="not_exists">不存在</option>
              <option value="greater_than">大于</option>
              <option value="less_than">小于</option>
            </select>
          </div>
          <div class="form-group">
            <label>期望值</label>
            <input v-model="newAssertion.expected" placeholder="期望值" />
          </div>
        </template>

        <!-- 响应时间 -->
        <template v-else-if="newAssertion.type === 'response_time'">
          <div class="form-group">
            <label>操作符</label>
            <select v-model="newAssertion.operator">
              <option value="less_than">小于</option>
              <option value="greater_than">大于</option>
            </select>
          </div>
          <div class="form-group">
            <label>期望时间 (ms)</label>
            <input v-model.number="newAssertion.expected" type="number" placeholder="1000" />
          </div>
        </template>

        <!-- 响应头 -->
        <template v-else-if="newAssertion.type === 'header'">
          <div class="form-group">
            <label>Header 名称</label>
            <input v-model="newAssertion.header_name" placeholder="Content-Type" />
          </div>
          <div class="form-group">
            <label>操作符</label>
            <select v-model="newAssertion.operator">
              <option value="equals">等于</option>
              <option value="contains">包含</option>
              <option value="exists">存在</option>
            </select>
          </div>
          <div class="form-group">
            <label>期望值</label>
            <input v-model="newAssertion.expected" placeholder="期望值" />
          </div>
        </template>

        <!-- 响应体包含 -->
        <template v-else-if="newAssertion.type === 'body_contains'">
          <div class="form-group">
            <label>操作符</label>
            <select v-model="newAssertion.operator">
              <option value="contains">包含</option>
              <option value="not_contains">不包含</option>
            </select>
          </div>
          <div class="form-group">
            <label>期望包含的文本</label>
            <input v-model="newAssertion.expected" placeholder="期望包含的文本" />
          </div>
        </template>

        <div class="form-actions">
          <button class="btn" @click="showAddModal = false">取消</button>
          <button class="btn primary" @click="confirmAdd">添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'run'])

const assertions = ref([...props.modelValue])
const showAddModal = ref(false)

const defaultNewAssertion = () => ({
  id: `assert_${Date.now()}`,
  type: 'status_code',
  operator: 'equals',
  expected: 200,
  enabled: true,
  path: '',
  header_name: '',
})

const newAssertion = ref(defaultNewAssertion())

// 生成唯一 ID
function generateId() {
  return `assert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 添加断言
function addAssertion() {
  newAssertion.value = defaultNewAssertion()
  showAddModal.value = true
}

// 确认添加
function confirmAdd() {
  const assertion = {
    id: generateId(),
    type: newAssertion.value.type,
    operator: newAssertion.value.operator,
    expected: newAssertion.value.expected,
    enabled: true,
    path: newAssertion.value.path || '',
    header_name: newAssertion.value.header_name || '',
  }
  assertions.value.push(assertion)
  updateModelValue()
  showAddModal.value = false
}

// 删除断言
function removeAssertion(index) {
  assertions.value.splice(index, 1)
  updateModelValue()
}

// 切换启用状态
function toggleAssertion(index) {
  assertions.value[index].enabled = !assertions.value[index].enabled
  updateModelValue()
}

// 类型变更时重置相关字段
function onTypeChange(assertion) {
  switch (assertion.type) {
    case 'status_code':
      assertion.operator = 'equals'
      assertion.expected = 200
      break
    case 'response_time':
      assertion.operator = 'less_than'
      assertion.expected = 1000
      break
    case 'json_path':
      assertion.operator = 'equals'
      assertion.path = '$.'
      assertion.expected = ''
      break
    case 'header':
      assertion.operator = 'contains'
      assertion.header_name = ''
      assertion.expected = ''
      break
    case 'body_contains':
      assertion.operator = 'contains'
      assertion.expected = ''
      break
  }
  updateModelValue()
}

// 更新父组件
function updateModelValue() {
  emit('update:modelValue', assertions.value.map(a => ({
    id: a.id,
    type: a.type,
    operator: a.operator,
    expected: a.expected,
    enabled: a.enabled,
    path: a.path || undefined,
    header_name: a.header_name || undefined,
  })))
}

// 显示测试结果
function showResults(results) {
  results.forEach(result => {
    const assertion = assertions.value.find(a => a.id === result.id)
    if (assertion) {
      assertion._result = result
      assertion._failed = !result.passed
    }
  })
}

// 清除结果
function clearResults() {
  assertions.value.forEach(a => {
    a._result = undefined
    a._failed = false
  })
}

// 监听外部值变化
watch(() => props.modelValue, (val) => {
  assertions.value = [...val]
}, { deep: true })

// 暴露方法
defineExpose({
  showResults,
  clearResults,
})
</script>

<style scoped>
.assertion-config {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.assertion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.btn-add {
  padding: 4px 10px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-add:hover {
  opacity: 0.9;
}

.empty-assertions {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
}

.assertion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assertion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}

.assertion-item.disabled {
  opacity: 0.5;
}

.assertion-item.failed {
  border-color: var(--danger);
  background: rgba(249, 62, 62, 0.05);
}

.assertion-toggle {
  flex-shrink: 0;
}

.assertion-toggle input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.assertion-type {
  flex-shrink: 0;
}

.assertion-type select {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 12px;
}

.assertion-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.assertion-content input,
.assertion-content select {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 12px;
}

.short-input {
  width: 80px;
}

.path-input {
  width: 140px;
  font-family: var(--mono);
}

.expected-input {
  flex: 1;
  min-width: 100px;
}

.expected-input.full {
  flex: none;
  width: 200px;
}

.unit {
  font-size: 12px;
  color: var(--text-secondary);
}

.assertion-result {
  flex-shrink: 0;
  font-size: 14px;
}

.btn-delete {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
}

.btn-delete:hover {
  background: var(--bg-secondary);
  color: var(--danger);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--bg);
  border-radius: 12px;
  padding: 20px;
  width: 400px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal h3 {
  margin: 0 0 16px;
  font-size: 15px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 13px;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text);
  cursor: pointer;
  font-size: 13px;
}

.btn.primary {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
</style>
