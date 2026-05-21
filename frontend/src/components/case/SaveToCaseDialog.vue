<template>
  <el-dialog
    v-model="dialogVisible"
    title="保存为用例"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="用例类型">
        <el-tag type="success">接口测试用例</el-tag>
      </el-form-item>

      <el-form-item label="用例名称" required>
        <el-input v-model="form.name" placeholder="请输入用例名称" />
      </el-form-item>

      <el-form-item label="用例编号">
        <el-input :model-value="suggestedCaseId" disabled />
      </el-form-item>

      <el-form-item label="所属分类">
        <el-select v-model="form.folder_id" placeholder="请选择分类" clearable style="width: 100%">
          <el-option
            v-for="folder in folders"
            :key="folder.id"
            :label="folder.name"
            :value="folder.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入描述" />
      </el-form-item>

      <el-form-item label="请求方法">
        <el-tag>{{ form.method }}</el-tag>
      </el-form-item>

      <el-form-item label="URL">
        <el-input v-model="form.url" disabled />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'
import { nextCaseCode } from '@/views/case/caseUtils'

const props = defineProps({
  modelValue: Boolean,
  requestData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  case_type: 'api',
  name: '',
  folder_id: null,
  description: '',
  method: 'GET',
  url: '',
  query_params: {},
  headers: {},
  cookies: {},
  body_type: 'none',
  body: '',
  auth_config: {},
  expected_status: null,
  source_debug_id: null,
})

const folders = ref([])
const existingCases = ref([])
const saving = ref(false)

const suggestedCaseId = computed(() => nextCaseCode(form.value.case_type, existingCases.value))

watch(() => props.requestData, (newData) => {
  if (newData) {
    const shouldUpdateName = !form.value.name || form.value.name === extractNameFromUrl(newData.url)
    form.value = {
      ...form.value,
      ...newData,
      name: shouldUpdateName && newData.url ? extractNameFromUrl(newData.url) : form.value.name,
    }
  }
}, { immediate: true })

watch(() => props.modelValue, (visible) => {
  if (visible) {
    loadFolders()
    loadExistingCases()
  }
})

function extractNameFromUrl(url) {
  try {
    const parsed = new URL(url)
    return parsed.pathname.split('/').filter(Boolean).slice(-1)[0] || '未命名用例'
  } catch {
    return '未命名用例'
  }
}

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({ case_type: form.value.case_type })
    folders.value = res.data.items
  } catch {
    console.error('加载分类失败')
  }
}

async function loadExistingCases() {
  try {
    const res = await caseApi.list({ case_type: form.value.case_type, page: 1, page_size: 500 })
    existingCases.value = res.data?.items || []
  } catch {
    existingCases.value = []
  }
}

async function handleSave() {
  if (!form.value.name) {
    ElMessage.warning('请输入用例名称')
    return
  }

  saving.value = true
  try {
    await caseApi.create(buildPayload())
    ElMessage.success('保存成功')
    emit('success')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function handleClose() {
  dialogVisible.value = false
}

function buildPayload() {
  return {
    case_type: form.value.case_type,
    name: form.value.name,
    folder_id: form.value.folder_id,
    description: form.value.description,
    priority: 'P2',
    tags: [],
    pre_condition: '',
    is_automated: false,
    auto_script_path: '',
    auto_script_config: {},
    auto_case_id: suggestedCaseId.value,
    source_debug_id: form.value.source_debug_id,
    api_case: {
      method: form.value.method,
      url: form.value.url,
      params: form.value.query_params || {},
      headers: form.value.headers || {},
      body_type: form.value.body_type || 'none',
      body: form.value.body || '',
      auth_config: form.value.auth_config || {},
      expected_status: form.value.expected_status || 200,
      assertions: [],
    },
  }
}
</script>
