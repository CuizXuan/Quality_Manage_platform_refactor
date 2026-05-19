<template>
  <div class="case-sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">用例分类</span>
      <el-button size="small" :icon="Plus" @click="handleCreateFolder">新建</el-button>
    </div>

    <div class="folder-search">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索分类"
        size="small"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <div class="folder-tree">
      <el-tree
        v-if="folderTree.length > 0"
        :data="folderTree"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        :expand-on-click-node="false"
        :filter-node-method="filterNode"
        :default-expand-all="true"
        ref="treeRef"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="folder-node">
            <el-icon><Folder /></el-icon>
            <span class="folder-name">{{ node.label }}</span>
          </span>
        </template>
      </el-tree>
      <el-empty v-else description="暂无分类" />
    </div>

    <el-dialog v-model="showFolderDialog" title="新建分类" width="400px">
      <el-form :model="folderForm" label-width="80px">
        <el-form-item label="分类名称">
          <el-input v-model="folderForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-tree-select
            v-if="showFolderDialog"
            v-model="folderForm.parent_id"
            :data="folderTree"
            :props="{ label: 'name', value: 'id' }"
            placeholder="选择上级分类（可选）"
            clearable
            :render-after-expand="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFolderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleDoCreateFolder">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Search, Folder, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'

const emit = defineEmits(['folder-selected'])

const searchKeyword = ref('')
const folderTree = ref([])
const treeRef = ref(null)
const showFolderDialog = ref(false)
const folderForm = ref({ name: '', parent_id: null })
const selectedFolderId = ref(null)

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({})
    folderTree.value = buildTree(res.data.items)
  } catch {
    ElMessage.error('加载分类失败')
  }
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

function filterNode(keyword, data) {
  if (!keyword) return true
  return data.name.includes(keyword)
}

function handleNodeClick(data) {
  // Only emit if clicking a different folder, ignore if same folder clicked
  if (selectedFolderId.value !== data.id) {
    selectedFolderId.value = data.id
    emit('folder-selected', data.id)
  }
}

function handleCreateFolder() {
  folderForm.value = { name: '', parent_id: null }
  showFolderDialog.value = true
}

async function handleDoCreateFolder() {
  if (!folderForm.value.name) {
    ElMessage.warning('请输入分类名称')
    return
  }
  try {
    await caseApi.createFolder(folderForm.value)
    ElMessage.success('创建成功')
    showFolderDialog.value = false
    loadFolders()
  } catch {
    ElMessage.error('创建失败')
  }
}

watch(searchKeyword, (val) => {
  if (treeRef.value) {
    treeRef.value.filter(val)
  }
})

onMounted(() => {
  loadFolders()
})

defineExpose({ reload: loadFolders })
</script>

<style scoped>
.case-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-title {
  font-weight: 600;
  color: var(--text-primary);
}

.folder-search {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
}

.folder-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.folder-node {
  display: flex;
  align-items: center;
  gap: 6px;
}

.folder-name {
  color: var(--text-primary);
}
</style>