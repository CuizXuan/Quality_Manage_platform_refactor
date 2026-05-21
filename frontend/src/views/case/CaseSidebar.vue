<template>
  <div class="case-sidebar">
    <div class="case-sidebar__header">
      <div>
        <span class="case-sidebar__title">{{ title }}</span>
        <span class="case-sidebar__meta">{{ subtitle }}</span>
      </div>
      <el-tooltip content="新建分类" placement="top">
        <el-button :icon="Plus" circle size="small" @click="openFolderDialog" />
      </el-tooltip>
    </div>

    <div class="case-sidebar__search">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索分类"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <el-scrollbar class="case-sidebar__tree">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        highlight-current
        default-expand-all
        :expand-on-click-node="false"
        :filter-node-method="filterNode"
        @node-click="selectFolder"
      >
        <template #default="{ node }">
          <span class="case-sidebar__node">
            <el-icon><Folder /></el-icon>
            <span class="text-ellipsis">{{ node.label }}</span>
          </span>
        </template>
      </el-tree>
    </el-scrollbar>

    <el-dialog
      v-model="showFolderDialog"
      title="新建分类"
      width="420px"
      append-to-body
      destroy-on-close
    >
      <el-form :model="folderForm" label-width="88px">
        <el-form-item label="分类名称">
          <el-input v-model="folderForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-tree-select
            v-model="folderForm.parent_id"
            :data="folderTree"
            :props="{ label: 'name', value: 'id' }"
            placeholder="请选择上级分类"
            clearable
            :render-after-expand="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFolderDialog = false">取消</el-button>
        <el-button type="primary" @click="createFolder">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Folder, Plus, Search } from '@element-plus/icons-vue'
import { caseApi } from '@/api/case'
import feedback from '@/utils/feedback'

const props = defineProps({
  caseType: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    default: '用例分类',
  },
  subtitle: {
    type: String,
    default: '按模块组织资产',
  },
})

const emit = defineEmits(['folder-selected'])

const folderTree = ref([])
const searchKeyword = ref('')
const selectedFolderId = ref(null)
const showFolderDialog = ref(false)
const treeRef = ref(null)
const folderForm = ref({
  name: '',
  parent_id: null,
})

const treeData = computed(() => [
  {
    id: 0,
    name: '全部分类',
    children: folderTree.value,
  },
])

function buildTree(folders) {
  const map = new Map()
  const roots = []

  folders.forEach((folder) => {
    map.set(folder.id, { ...folder, children: [] })
  })

  folders.forEach((folder) => {
    const item = map.get(folder.id)
    const parent = map.get(folder.parent_id)
    if (parent) {
      parent.children.push(item)
      return
    }
    roots.push(item)
  })

  return roots
}

async function loadFolders() {
  try {
    const response = await caseApi.listFolders({ case_type: props.caseType })
    folderTree.value = buildTree(response.data.items || [])
  } catch {
    feedback.error('加载分类失败')
  }
}

function filterNode(keyword, data) {
  if (!keyword) return true
  return data.name.includes(keyword)
}

function selectFolder(data) {
  selectedFolderId.value = data.id || null
  emit('folder-selected', selectedFolderId.value)
}

function openFolderDialog() {
  folderForm.value = {
    name: '',
    parent_id: selectedFolderId.value,
  }
  showFolderDialog.value = true
}

async function createFolder() {
  if (!folderForm.value.name.trim()) {
    feedback.warning('请输入分类名称')
    return
  }

  try {
    await caseApi.createFolder({
      ...folderForm.value,
      case_type: props.caseType,
    })
    feedback.success('分类创建成功')
    showFolderDialog.value = false
    loadFolders()
  } catch {
    feedback.error('分类创建失败')
  }
}

watch(searchKeyword, (value) => {
  treeRef.value?.filter(value)
})

watch(() => props.caseType, () => {
  selectedFolderId.value = null
  loadFolders()
})

onMounted(loadFolders)

defineExpose({ reload: loadFolders })
</script>

<style scoped>
.case-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.case-sidebar__header {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: center;
  min-height: 68px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.case-sidebar__title,
.case-sidebar__meta {
  display: block;
}

.case-sidebar__title {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 700;
}

.case-sidebar__meta {
  margin-top: var(--spacing-xs);
  color: var(--text-secondary);
  font-size: 12px;
}

.case-sidebar__search {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.case-sidebar__tree {
  flex: 1;
  min-height: 0;
  padding: 8px 10px 12px;
}

.case-sidebar__node {
  display: inline-flex;
  min-width: 0;
  gap: var(--spacing-sm);
  align-items: center;
  color: var(--text-primary);
}

.case-sidebar :deep(.el-tree-node__content) {
  height: 34px;
  border-radius: var(--border-radius-base);
  transition: all 0.2s ease;
}

.case-sidebar :deep(.el-tree-node__content:hover) {
  background: var(--bg-container-soft);
}

.case-sidebar :deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 700;
}
</style>
