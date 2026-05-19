<template>
  <div class="case-detail">
    <div class="detail-header">
      <span class="detail-title">{{ isNew ? '新建用例' : '编辑用例' }}</span>
      <div class="detail-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </div>
    </div>

    <el-form :model="caseForm" label-width="100px" class="detail-form">
      <el-form-item label="用例名称" required>
        <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
      </el-form-item>

      <el-form-item label="用例类型">
        <el-radio-group v-model="caseForm.case_type" :disabled="!isNew">
          <el-radio v-for="item in caseTypeOptions" :key="item.code" :label="item.code">
            {{ item.name }}
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="所属分类">
        <el-tree-select
          v-model="caseForm.folder_id"
          :data="folderTree"
          :props="{ label: 'name', value: 'id' }"
          placeholder="选择分类"
          clearable
          :render-after-expand="false"
        />
      </el-form-item>

      <el-form-item label="优先级">
        <el-select v-model="caseForm.priority" style="width: 150px">
          <el-option v-for="item in priorityOptions" :key="item.code" :label="item.name" :value="item.code" />
        </el-select>
      </el-form-item>

      <el-form-item label="标签">
        <el-select v-model="caseForm.tags" multiple placeholder="选择标签" style="width: 100%">
          <el-option v-for="item in tagOptions" :key="item.code" :label="item.name" :value="item.code" />
        </el-select>
      </el-form-item>

      <el-form-item label="前置条件">
        <RichTextEditor v-model="caseForm.pre_condition" />
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="caseForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
      </el-form-item>

      <el-divider content-position="left">类型特有字段</el-divider>

      <ApiCaseForm v-if="caseForm.case_type === 'api'" :key="'api-' + caseForm.id" v-model="caseForm.api_case" />
      <FunctionalCaseForm v-else :key="'func-' + caseForm.id" v-model="caseForm.functional_case" />
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useCaseStore } from '@/stores/caseStore'
import { caseApi } from '@/api/case'
import { systemApi } from '@/api/system'
import ApiCaseForm from './ApiCaseForm.vue'
import FunctionalCaseForm from './FunctionalCaseForm.vue'
import RichTextEditor from '@/components/common/RichTextEditor.vue'

const props = defineProps({
  caseData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['saved', 'deleted'])

const caseStore = useCaseStore()
const folderTree = ref([])
const allDictionaries = ref([])

const priorityOptions = computed(() =>
  allDictionaries.value
    .filter(d => d.category === 'priority')
    .sort((a, b) => a.sort_order - b.sort_order)
)

const caseTypeOptions = computed(() =>
  allDictionaries.value
    .filter(d => d.category === 'case_type')
    .sort((a, b) => a.sort_order - b.sort_order)
)

const tagOptions = computed(() =>
  allDictionaries.value
    .filter(d => d.category === 'tag')
    .sort((a, b) => a.sort_order - b.sort_order)
)

const isNew = computed(() => !props.caseData?.id)
const caseForm = ref({
  name: '',
  case_type: 'api',
  folder_id: null,
  priority: 'P2',
  tags: [],
  pre_condition: '',
  description: '',
  api_case: {},
  functional_case: {},
})

watch(() => props.caseData, (val) => {
  if (val?.id) {
    caseForm.value = {
      ...caseForm.value,
      ...val,
      tags: val.tags || [],
    }
  } else {
    caseForm.value = {
      name: '',
      case_type: 'api',
      folder_id: null,
      priority: 'P2',
      tags: [],
      pre_condition: '',
      description: '',
      api_case: {},
      functional_case: {},
    }
  }
}, { immediate: true })

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({})
    folderTree.value = buildTree(res.data.items)
  } catch {}
}

async function loadDictionaries() {
  try {
    const res = await systemApi.dictionaries.list()
    allDictionaries.value = res.data
  } catch {}
}

function buildTree(folders) {
  const map = {}
  const roots = []
  folders.forEach(f => {
    map[f.id] = { ...f, children: [] }
  })
  folders.forEach(f => {
    if (f.parent_id && map[f.parent_id]) {
      map[f.parent_id].children.push(map[f.id])
    } else {
      roots.push(map[f.id])
    }
  })
  return roots
}

async function handleSave() {
  if (!caseForm.value.name) {
    return
  }
  try {
    if (isNew.value) {
      await caseApi.create(caseForm.value)
    } else {
      await caseApi.update(props.caseData.id, caseForm.value)
    }
    emit('saved')
  } catch {}
}

function handleCancel() {
  emit('deleted')
}

onMounted(() => {
  loadFolders()
  loadDictionaries()
})
</script>

<style scoped>
.case-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.detail-title {
  font-weight: 600;
  color: var(--text-primary);
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-form {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
</style>
