<template>
  <div class="case-detail">
    <el-form :model="caseForm" label-width="100px" class="detail-form">
      <el-form-item label="用例名称" required>
        <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
      </el-form-item>

      <el-form-item label="用例类型">
        <el-radio-group v-model="caseForm.case_type" :disabled="!isNew">
          <el-radio v-for="item in caseTypeOptions" :key="item.code" :value="item.code">
            {{ item.label }}
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
          <el-option v-for="item in priorityOptions" :key="item.code" :label="item.label" :value="item.code" />
        </el-select>
      </el-form-item>

      <el-form-item label="标签">
        <el-select v-model="caseForm.tags" multiple placeholder="选择标签" style="width: 100%">
          <el-option v-for="item in tagOptions" :key="item.code" :label="item.label" :value="item.code" />
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
import { caseApi } from '@/api/case'
import { dictPublicApi } from '@/api/dictionary'
import ApiCaseForm from './ApiCaseForm.vue'
import FunctionalCaseForm from './FunctionalCaseForm.vue'
import RichTextEditor from '@/components/common/RichTextEditor.vue'

function createDefaultApiCase() {
  return {
    method: 'GET',
    url: '',
    headers: [],
    params: [],
    body_type: 'none',
    body: '',
    auth_config: {},
    expected_status: 200,
    assertions: [],
  }
}

function createDefaultFunctionalCase() {
  return {
    steps: [],
    test_data: {},
    post_action: '',
    expected_result: '',
  }
}

const props = defineProps({
  caseData: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['saved', 'deleted'])

const folderTree = ref([])
const allDictTypes = ref([])

const priorityOptions = computed(() =>
  allDictTypes.value
    .find(t => t.code === 'priority')?.items || [],
)

const caseTypeOptions = computed(() =>
  allDictTypes.value
    .find(t => t.code === 'case_type')?.items || [],
)

const tagOptions = computed(() =>
  allDictTypes.value
    .find(t => t.code === 'tag')?.items || [],
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
  api_case: createDefaultApiCase(),
  functional_case: createDefaultFunctionalCase(),
})

watch(
  () => props.caseData,
  (val) => {
    if (val?.id) {
      caseForm.value = {
        ...caseForm.value,
        ...val,
        tags: val.tags || [],
        api_case: {
          ...createDefaultApiCase(),
          ...(val.api_case || {}),
        },
        functional_case: {
          ...createDefaultFunctionalCase(),
          ...(val.functional_case || {}),
        },
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
        api_case: createDefaultApiCase(),
        functional_case: createDefaultFunctionalCase(),
      }
    }
  },
  { immediate: true },
)

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({})
    folderTree.value = buildTree(res.data.items)
  } catch {}
}

async function loadDictionaries() {
  try {
    const res = await dictPublicApi.getAll()
    allDictTypes.value = res.data.types || []
  } catch {}
}

function buildTree(folders) {
  const map = {}
  const roots = []
  folders.forEach((folder) => {
    map[folder.id] = { ...folder, children: [] }
  })
  folders.forEach((folder) => {
    if (folder.parent_id && map[folder.parent_id]) {
      map[folder.parent_id].children.push(map[folder.id])
    } else {
      roots.push(map[folder.id])
    }
  })
  return roots
}

async function handleSave() {
  if (!caseForm.value.name) return
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

defineExpose({
  handleSave,
  handleCancel,
})
</script>

<style scoped>
.case-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-container);
}

.detail-form {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px 16px;
}
</style>
