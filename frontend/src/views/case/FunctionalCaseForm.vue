<template>
  <div class="functional-case-form">
    <el-form :model="modelValue" label-width="96px">
      <el-form-item label="测试步骤">
        <div class="functional-case-form__steps">
          <div class="functional-case-form__parser">
            <div class="functional-case-form__templates">
              <span>常用模板</span>
              <el-button
                v-for="template in stepTemplates"
                :key="template.name"
                size="small"
                plain
                @click="applyTemplate(template)"
              >
                {{ template.name }}
              </el-button>
            </div>
            <el-input
              v-model="stepText"
              type="textarea"
              :rows="3"
              placeholder="粘贴步骤文本，支持用分号、中文分号或换行分隔；动作和预期可用 =>、->、： 分开"
            />
            <div class="functional-case-form__parser-actions">
              <el-button :icon="MagicStick" @click="parseStepText">识别填充</el-button>
              <el-button text @click="stepText = ''">清空文本</el-button>
            </div>
          </div>

          <el-table :data="modelValue.steps" border>
            <el-table-column label="#" width="72" align="center">
              <template #default="{ $index }">{{ $index + 1 }}</template>
            </el-table-column>
            <el-table-column label="动作" min-width="260">
              <template #default="{ row }">
                <el-input v-model="row.description" placeholder="请输入操作动作" />
              </template>
            </el-table-column>
            <el-table-column label="预期结果" min-width="260">
              <template #default="{ row }">
                <el-input v-model="row.expected_result" placeholder="请输入预期结果" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" align="center">
              <template #default="{ $index }">
                <div class="functional-case-form__actions">
                  <el-tooltip content="上移" placement="top">
                    <el-button
                      text
                      :icon="ArrowUp"
                      :disabled="$index === 0"
                      @click="moveStep($index, -1)"
                    />
                  </el-tooltip>
                  <el-tooltip content="下移" placement="top">
                    <el-button
                      text
                      :icon="ArrowDown"
                      :disabled="$index === modelValue.steps.length - 1"
                      @click="moveStep($index, 1)"
                    />
                  </el-tooltip>
                  <el-tooltip content="删除" placement="top">
                    <el-button text type="danger" :icon="Delete" @click="removeStep($index)" />
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-button :icon="Plus" @click="addStep">新增步骤</el-button>
        </div>
      </el-form-item>

      <el-form-item label="测试数据">
        <el-input
          v-model="testDataText"
          type="textarea"
          :rows="5"
          placeholder='请输入 JSON，例如 {"username": "demo"}'
          @blur="parseTestData"
        />
      </el-form-item>
      <el-form-item label="后置动作">
        <RichTextEditor v-model="modelValue.post_action" />
      </el-form-item>
      <el-form-item label="预期结果">
        <RichTextEditor v-model="modelValue.expected_result" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ArrowDown, ArrowUp, Delete, MagicStick, Plus } from '@element-plus/icons-vue'
import RichTextEditor from '@/components/common/RichTextEditor.vue'
import feedback from '@/utils/feedback'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
})

const testDataText = ref('{}')
const stepText = ref('')
const stepTemplates = [
  {
    name: '登录流程',
    steps: [
      ['打开登录页', '登录页展示正常'],
      ['输入有效账号和密码', '输入内容被正确回显或隐藏'],
      ['点击登录按钮', '进入工作台且无错误提示'],
    ],
  },
  {
    name: '查询流程',
    steps: [
      ['进入目标列表页', '列表加载完成'],
      ['输入查询条件并点击查询', '展示符合条件的数据'],
      ['点击重置', '筛选条件清空且列表恢复默认'],
    ],
  },
  {
    name: '表单提交',
    steps: [
      ['打开新增表单', '表单字段展示完整'],
      ['填写必填项并提交', '保存成功并关闭弹窗'],
      ['返回列表检查数据', '新数据出现在列表中'],
    ],
  },
]

function syncTestDataText() {
  testDataText.value = JSON.stringify(props.modelValue.test_data || {}, null, 2)
}

function addStep() {
  props.modelValue.steps.push({
    order: props.modelValue.steps.length + 1,
    description: '',
    expected_result: '',
    test_data: {},
  })
}

function createStep(description, expectedResult = '') {
  return {
    order: props.modelValue.steps.length + 1,
    description,
    expected_result: expectedResult,
    test_data: {},
  }
}

function parseStepText() {
  const items = splitStepText(stepText.value)
  if (!items.length) {
    feedback.warning('请输入可识别的步骤文本')
    return
  }

  props.modelValue.steps.splice(0, props.modelValue.steps.length)
  items.forEach((item) => {
    props.modelValue.steps.push(createStep(item.description, item.expected_result))
  })
  resetStepOrder()
  feedback.success('步骤识别完成')
}

function applyTemplate(template) {
  props.modelValue.steps.splice(0, props.modelValue.steps.length)
  template.steps.forEach(([description, expectedResult]) => {
    props.modelValue.steps.push(createStep(description, expectedResult))
  })
  resetStepOrder()
  feedback.success(`已填充${template.name}模板`)
}

function splitStepText(value) {
  return String(value || '')
    .split(/[；;\n\r]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map(parseStepLine)
}

function parseStepLine(line) {
  const normalized = line.replace(/^步骤\s*\d+\s*[：:.、-]?\s*/i, '')
  const parts = normalized.split(/\s*(?:=>|->|→|预期[:：]|期望[:：])\s*/)
  if (parts.length > 1) {
    return {
      description: parts[0].trim(),
      expected_result: parts.slice(1).join(' ').trim(),
    }
  }

  const colonParts = normalized.split(/[：:]/)
  if (colonParts.length > 1 && colonParts[0].length <= 8) {
    return {
      description: colonParts.slice(1).join(':').trim(),
      expected_result: '',
    }
  }

  return {
    description: normalized,
    expected_result: '',
  }
}

function removeStep(index) {
  props.modelValue.steps.splice(index, 1)
  resetStepOrder()
}

function moveStep(index, direction) {
  const nextIndex = index + direction
  const steps = props.modelValue.steps
  if (!steps[nextIndex]) return
  const current = steps[index]
  steps[index] = steps[nextIndex]
  steps[nextIndex] = current
  resetStepOrder()
}

function resetStepOrder() {
  props.modelValue.steps.forEach((step, index) => {
    step.order = index + 1
  })
}

function parseTestData() {
  if (!testDataText.value.trim()) {
    props.modelValue.test_data = {}
    return
  }

  try {
    props.modelValue.test_data = JSON.parse(testDataText.value)
    syncTestDataText()
  } catch {
    feedback.warning('测试数据必须是有效 JSON')
  }
}

watch(() => props.modelValue.test_data, syncTestDataText, { immediate: true, deep: true })
</script>

<style scoped>
.functional-case-form {
  display: grid;
  gap: var(--spacing-md);
}

.functional-case-form__steps {
  display: grid;
  width: 100%;
  gap: var(--spacing-sm);
}

.functional-case-form__parser {
  display: grid;
  gap: var(--spacing-sm);
  padding: 10px 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.functional-case-form__templates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.functional-case-form__templates span {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 800;
}

.functional-case-form__parser-actions,
.functional-case-form__actions {
  display: flex;
  align-items: center;
}

.functional-case-form__parser-actions {
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.functional-case-form__actions {
  justify-content: center;
  gap: var(--spacing-xs);
  white-space: nowrap;
}

.functional-case-form__actions :deep(.el-button) {
  width: 28px;
  height: 28px;
  margin-left: 0;
  padding: 0;
}

.functional-case-form :deep(.el-table__header th) {
  background: var(--bg-container-soft);
  color: var(--text-secondary);
}

.functional-case-form :deep(.el-table__body td) {
  background: var(--bg-container);
}

.functional-case-form :deep(.el-table .cell) {
  overflow: visible;
}

.functional-case-form :deep(.el-table__cell) {
  vertical-align: middle;
}

.functional-case-form :deep(.el-input) {
  width: 100%;
}

.functional-case-form__steps > .el-button {
  justify-self: start;
}
</style>
