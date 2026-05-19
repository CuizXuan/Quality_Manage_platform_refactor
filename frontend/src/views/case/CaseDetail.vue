<template>
  <div class="case-detail-container">
    <div v-if="!currentCase" class="empty-state">
      <el-empty description="请选择一个用例查看详情" />
    </div>

    <div v-else class="detail-content">
      <div class="detail-header">
        <h3>用例详情</h3>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>

      <el-form :model="formData" label-width="120px" class="case-form">
        <el-form-item label="用例名称" required>
          <el-input v-model="formData.name" placeholder="请输入用例名称" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>

        <el-form-item label="请求方法" required>
          <el-select v-model="formData.method" style="width: 150px">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>

        <el-form-item label="URL" required>
          <el-input v-model="formData.url" placeholder="请输入请求URL" />
        </el-form-item>

        <el-form-item label="Query参数">
          <el-input
            v-model="queryParamsText"
            type="textarea"
            :rows="3"
            placeholder="JSON格式，如: {&quot;key&quot;: &quot;value&quot;}"
          />
        </el-form-item>

        <el-form-item label="请求头">
          <el-input
            v-model="headersText"
            type="textarea"
            :rows="3"
            placeholder="JSON格式，如: {&quot;Content-Type&quot;: &quot;application/json&quot;}"
          />
        </el-form-item>

        <el-form-item label="Cookie">
          <el-input
            v-model="cookiesText"
            type="textarea"
            :rows="2"
            placeholder="JSON格式，如: {&quot;session&quot;: &quot;abc123&quot;}"
          />
        </el-form-item>

        <el-form-item label="认证配置">
          <el-input
            v-model="authConfigText"
            type="textarea"
            :rows="2"
            placeholder="JSON格式，如: {&quot;type&quot;: &quot;bearer&quot;, &quot;token&quot;: &quot;...&quot;}"
          />
        </el-form-item>

        <el-form-item label="Body类型">
          <el-select v-model="formData.body_type" style="width: 150px">
            <el-option label="无" value="none" />
            <el-option label="JSON" value="json" />
            <el-option label="Form" value="form" />
            <el-option label="Raw" value="raw" />
          </el-select>
        </el-form-item>

        <el-form-item label="Body内容">
          <el-input
            v-model="formData.body"
            type="textarea"
            :rows="4"
            placeholder="请求体内容"
          />
        </el-form-item>

        <el-form-item label="期望状态码">
          <el-input-number v-model="formData.expected_status" :min="100" :max="599" placeholder="如: 200" />
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useCaseStore } from '@/stores/caseStore'

const props = defineProps({
  caseData: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['saved'])

const caseStore = useCaseStore()
const saving = ref(false)

const currentCase = computed(() => props.caseData)

const formData = ref({
  name: '',
  description: '',
  method: 'GET',
  url: '',
  query_params: {},
  headers: {},
  cookies: {},
  auth_config: {},
  body_type: 'none',
  body: '',
  expected_status: null,
})

// JSON editors
const queryParamsText = ref('{}')
const headersText = ref('{}')
const cookiesText = ref('{}')
const authConfigText = ref('{}')

watch(
  () => props.caseData,
  (newCase) => {
    if (newCase) {
      formData.value = {
        name: newCase.name || '',
        description: newCase.description || '',
        method: newCase.method || 'GET',
        url: newCase.url || '',
        query_params: newCase.query_params || {},
        headers: newCase.headers || {},
        cookies: newCase.cookies || {},
        auth_config: newCase.auth_config || {},
        body_type: newCase.body_type || 'none',
        body: newCase.body || '',
        expected_status: newCase.expected_status || null,
      }
      queryParamsText.value = JSON.stringify(newCase.query_params || {}, null, 2)
      headersText.value = JSON.stringify(newCase.headers || {}, null, 2)
      cookiesText.value = JSON.stringify(newCase.cookies || {}, null, 2)
      authConfigText.value = JSON.stringify(newCase.auth_config || {}, null, 2)
    }
  },
  { immediate: true },
)

async function handleSave() {
  if (!formData.value.name || !formData.value.url) {
    ElMessage.warning('请填写必填项')
    return
  }

  // Parse JSON fields
  try {
    formData.value.query_params = JSON.parse(queryParamsText.value || '{}')
    formData.value.headers = JSON.parse(headersText.value || '{}')
    formData.value.cookies = JSON.parse(cookiesText.value || '{}')
    formData.value.auth_config = JSON.parse(authConfigText.value || '{}')
  } catch {
    ElMessage.error('JSON格式错误')
    return
  }

  saving.value = true
  try {
    await caseStore.updateCase(currentCase.value.id, formData.value)
    ElMessage.success('保存成功')
    emit('saved')
  } catch {
    ElMessage.error(caseStore.error || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.case-detail-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h3 {
  margin: 0;
}

.case-form {
  max-width: 800px;
}
</style>
