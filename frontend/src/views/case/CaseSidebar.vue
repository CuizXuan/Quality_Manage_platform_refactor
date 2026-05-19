<template>
  <div class="case-sidebar">
    <div class="sidebar-tabs">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="功能测试" name="functional" />
        <el-tab-pane label="接口测试" name="api" />
      </el-tabs>
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
        :data="folderTree"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        :expand-on-click-node="false"
        :filter-node-method="filterNode"
        ref="treeRef"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="folder-node">
            <el-icon><Folder /></el-icon>
            <span>{{ node.label }}</span>
            <span class="case-count">({{ data.case_count || 0 }})</span>
          </span>
        </template>
      </el-tree>
    </div>

    <div class="sidebar-footer">
      <el-button size="small" :icon="Plus" @click="handleCreateFolder">新建分类</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Search, Folder, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'

const props = defineProps({
  caseType: {
    type: String,
    default: 'api'
  }
})

const emit = defineEmits(['folder-selected', 'case-type-change'])

const activeTab = ref(props.caseType)
const searchKeyword = ref('')
const folderTree = ref([])
const treeRef = ref(null)

watch(() => props.caseType, (newType) => {
  activeTab.value = newType
  loadFolders()
}, { immediate: true })

function handleTabChange(tab) {
  emit('case-type-change', tab)
  loadFolders()
}

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({ case_type: activeTab.value })
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
  emit('folder-selected', data.id)
}

watch(searchKeyword, (val) => {
  treeRef.value?.filter(val)
})

function handleCreateFolder() {
  // TODO: 弹出创建分类对话框
}

defineExpose({
  reload: loadFolders,
})

onMounted(() => {
  loadFolders()
})
</script>

<style scoped>
.case-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-container);
}

.sidebar-tabs {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
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
  gap: 4px;
}

.case-count {
  color: var(--text-secondary);
  font-size: 12px;
}

.sidebar-footer {
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
}
</style>