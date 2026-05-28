<template>
  <div class="variant-list-container">
    <div class="header">
      <h4>用例变体</h4>
      <div class="header-actions">
        <el-button type="primary" size="small" :icon="MagicStick" :loading="aiGenerating" @click="handleAiGenerateVariants">AI 生成变体</el-button>
        <el-button type="primary" size="small" @click="showCreateDialog = true">新建变体</el-button>
      </div>
    </div>

    <!-- AI 变体建议弹窗 -->
    <el-dialog v-model="aiVariantsVisible" title="AI 变体建议" width="600px" destroy-on-close>
      <div v-if="aiVariantSuggestions.length" class="variant-suggestions">
        <div v-for="(v, i) in aiVariantSuggestions" :key="i" class="variant-suggestion-item">
          <div class="variant-info">
            <el-tag size="small" type="primary">{{ v.variant_type }}</el-tag>
            <span class="variant-desc">{{ v.description }}</span>
          </div>
          <el-button type="primary" size="small" @click="acceptVariant(v)">采纳</el-button>
        </div>
      </div>
      <el-empty v-else-if="!aiGenerating" description="暂无变体建议" />
      <div v-else class="ai-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>AI 正在生成变体...</span>
      </div>
      <template #footer>
        <el-button @click="aiVariantsVisible = false">关闭</el-button>
        <el-button type="primary" @click="acceptAllVariants" :disabled="!aiVariantSuggestions.length">采纳全部</el-button>
      </template>
    </el-dialog>

    <el-table
      v-loading="loading"
      :data="variants"
      height="100%"
      highlight-current-row
      empty-text="暂无变体"
    >
      <el-table-column prop="name" label="变体名称" min-width="150">
        <template #default="{ row }">
          <span :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="variant_type" label="变体类型" width="150">
        <template #default="{ row }">
          <el-tag size="small">{{ row.variant_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="expected_status" label="期望状态码" width="120">
        <template #default="{ row }">
          {{ row.expected_status || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="total"
      :page-sizes="[15, 30, 50, 100]"
      layout="total, prev, pager, next"
      style="margin-top: 12px"
      small
      @current-change="loadVariants"
      @size-change="loadVariants"
    />

    <!-- Create Variant Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建变体" width="600px">
      <el-form :model="variantForm" label-width="120px">
        <el-form-item label="变体名称" required>
          <el-input v-model="variantForm.name" placeholder="请输入变体名称" />
        </el-form-item>

        <el-form-item label="变体类型" required>
          <el-select v-model="variantForm.variant_type" placeholder="请选择变体类型">
            <el-option
              v-for="type in variantTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="覆盖参数">
          <el-input
            v-model="variantForm.override_params"
            type="textarea"
            :rows="2"
            placeholder="JSON格式"
          />
        </el-form-item>

        <el-form-item label="覆盖请求头">
          <el-input
            v-model="variantForm.override_headers"
            type="textarea"
            :rows="2"
            placeholder="JSON格式"
          />
        </el-form-item>

        <el-form-item label="覆盖Body">
          <el-input
            v-model="variantForm.override_body"
            type="textarea"
            :rows="3"
            placeholder="覆盖请求体内容"
          />
        </el-form-item>

        <el-form-item label="期望状态码">
          <el-input-number v-model="variantForm.expected_status" :min="100" :max="599" />
        </el-form-item>

        <el-form-item label="断言配置">
          <el-input
            v-model="variantForm.assertions"
            type="textarea"
            :rows="3"
            placeholder="JSON数组格式"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Loading } from '@element-plus/icons-vue'
import { useCaseStore } from '@/stores/caseStore'
import { useAiStore } from '@/stores/aiStore'

const props = defineProps({
  caseId: {
    type: Number,
    required: true,
  },
})

const caseStore = useCaseStore()

const variants = ref([])
const total = ref(0)
const currentPage = ref(1)
const currentPageSize = ref(20)
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)

const variantTypes = [
  'normal',
  'boundary',
  'empty',
  'missing_field',
  'type_error',
  'invalid_enum',
  'overlong_field',
  'auth_failed',
  'permission_denied',
  'response_schema',
  'response_business_value',
  'performance_threshold',
]

const variantForm = ref({
  name: '',
  variant_type: '',
  override_params: '{}',
  override_headers: '{}',
  override_body: '',
  expected_status: null,
  assertions: '[]',
})

watch(
  () => props.caseId,
  (newId) => {
    if (newId) {
      loadVariants()
    }
  },
  { immediate: true },
)

async function loadVariants() {
  if (!props.caseId) return
  loading.value = true
  try {
    await caseStore.fetchVariants(props.caseId, {
      page: currentPage.value,
      page_size: currentPageSize.value,
    })
    variants.value = caseStore.variants
    total.value = caseStore.variantTotal
  } catch {
    ElMessage.error(caseStore.error || '加载变体失败')
  } finally {
    loading.value = false
  }
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return timeStr.replace('T', ' ').substring(0, 19)
}

async function handleCreate() {
  if (!variantForm.value.name || !variantForm.value.variant_type) {
    ElMessage.warning('请填写必填项')
    return
  }

  creating.value = true
  try {
    const data = {
      name: variantForm.value.name,
      variant_type: variantForm.value.variant_type,
      override_params: JSON.parse(variantForm.value.override_params || '{}'),
      override_headers: JSON.parse(variantForm.value.override_headers || '{}'),
      override_body: variantForm.value.override_body,
      expected_status: variantForm.value.expected_status,
      assertions: JSON.parse(variantForm.value.assertions || '[]'),
    }
    await caseStore.createVariant(props.caseId, data)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    // Reset form
    variantForm.value = {
      name: '',
      variant_type: '',
      override_params: '{}',
      override_headers: '{}',
      override_body: '',
      expected_status: null,
      assertions: '[]',
    }
    loadVariants()
  } catch {
    ElMessage.error(caseStore.error || '创建失败')
  } finally {
    creating.value = false
  }
}

// ── AI 变体生成 ────────────────────────────────────────────

const aiStore = useAiStore()
const aiGenerating = ref(false)
const aiVariantsVisible = ref(false)
const aiVariantSuggestions = ref([])

async function handleAiGenerateVariants() {
  if (!props.caseId) {
    ElMessage.warning('用例 ID 无效')
    return
  }
  aiGenerating.value = true
  aiVariantSuggestions.value = []
  aiVariantsVisible.value = true
  try {
    const result = await aiStore.generateVariants({ case_id: props.caseId })
    if (result?.variants?.length) {
      aiVariantSuggestions.value = result.variants
      ElMessage.success(`生成 ${result.variants.length} 条变体建议`)
    } else {
      ElMessage.warning('未生成变体建议')
    }
  } catch (e) {
    ElMessage.error('AI 生成失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiGenerating.value = false
  }
}

function acceptVariant(v) {
  const vtype = typeof v.variant_type === 'string' ? v.variant_type : 'normal'
  const overrideConfig = typeof v.override_config === 'object' && v.override_config !== null ? v.override_config : {}

  creating.value = true
  caseStore.createVariant(props.caseId, {
    name: 'AI 变体 - ' + vtype,
    variant_type: vtype,
    override_params: overrideConfig.params || overrideConfig.override || {},
    override_headers: overrideConfig.headers || {},
    override_body: typeof overrideConfig.body === 'string' ? overrideConfig.body : JSON.stringify(overrideConfig.body || {}),
    expected_status: overrideConfig.expected_status || null,
    assertions: [],
  }).then(() => {
    ElMessage.success('已创建变体')
    aiVariantSuggestions.value = aiVariantSuggestions.value.filter(x => x !== v)
    if (aiVariantSuggestions.value.length === 0) {
      aiVariantsVisible.value = false
    }
    loadVariants()
  }).catch(e => {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  }).finally(() => {
    creating.value = false
  })
}

async function acceptAllVariants() {
  for (const v of [...aiVariantSuggestions.value]) {
    await caseStore.createVariant(props.caseId, {
      name: 'AI 变体 - ' + (typeof v.variant_type === 'string' ? v.variant_type : 'normal'),
      variant_type: typeof v.variant_type === 'string' ? v.variant_type : 'normal',
      override_params: (typeof v.override_config === 'object' && v.override_config !== null ? v.override_config.params : {}) || {},
      override_headers: (typeof v.override_config === 'object' && v.override_config !== null ? v.override_config.headers : {}) || {},
      override_body: '',
      expected_status: null,
      assertions: [],
    })
  }
  aiVariantSuggestions.value = []
  aiVariantsVisible.value = false
  ElMessage.success('已批量创建变体')
  loadVariants()
}

defineExpose({
  reload: loadVariants,
})
</script>

<style scoped>
.variant-list-container {
  padding: 12px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header h4 {
  margin: 0;
}

.variant-suggestions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variant-suggestion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: var(--border-radius-base);
}

.variant-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.variant-desc {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: var(--text-secondary);
  justify-content: center;
}
</style>
