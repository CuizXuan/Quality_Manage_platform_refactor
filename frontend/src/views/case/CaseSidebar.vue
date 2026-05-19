<template>
  <div class="case-sidebar">
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
import { useRoute } from 'vue-router'
import { Search, Folder, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'

const route = useRoute()

const emit = defineEmits(['folder-selected'])

const searchKeyword = ref('')
const folderTree = ref([])
const treeRef = ref(null)

// caseType 由路由路径决定：/case/functional 或 /case/api
const caseType = route.path.includes('functional') ? 'functional' : 'api'

watch(() => route.path, () => {
  loadFolders()
}, { immediate: true })

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({ case_type: caseType })
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