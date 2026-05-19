<template>
  <div class="folder-manager">
    <div class="toolbar">
      <el-button type="primary" size="small" @click="dialogRef?.open()">+ 新增分类</el-button>
    </div>
    <el-table :data="folders" v-loading="loading" class="cyber-table mt-2">
      <el-table-column prop="name" label="分类名称" min-width="150" />
      <el-table-column prop="sort_order" label="排序" width="100" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="openEdit(row)">编辑</el-button>
          <el-button size="small" link type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <CaseFolderDialog ref="dialogRef" @refresh="fetchFolders" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCaseFolders, deleteCaseFolder } from '@/api/caseFolders'
import { ElMessage, ElMessageBox } from 'element-plus'
import CaseFolderDialog from './CaseFolderDialog.vue'

const folders = ref<any[]>([])
const loading = ref(false)
const dialogRef = ref<any>(null)

async function fetchFolders() {
  loading.value = true
  try {
    const { data } = await getCaseFolders()
    folders.value = data
  } catch {
    ElMessage.error('加载分类失败')
  } finally {
    loading.value = false
  }
}

function openEdit(row: any) {
  dialogRef.value?.open(row)
}

async function confirmDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类「${row.name}」吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await deleteCaseFolder(row.id)
    ElMessage.success('删除成功')
    fetchFolders()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(fetchFolders)
</script>

<style scoped>
.folder-manager { padding: 0; }
.toolbar {
  margin-bottom: 8px;
  padding-top: 16px;
}
.mt-2 { margin-top: 8px; }

:deep(.el-table) {
  --el-table-bg-color: var(--bg-panel, #0d0d14);
  --el-table-tr-bg-color: var(--bg-panel, #0d0d14);
  --el-table-header-bg-color: var(--bg-secondary, #0a0a0f);
  --el-table-header-text-color: var(--neon-cyan, #0ff);
  --el-table-text-color: var(--text-primary, #e0e0e0);
  --el-table-border-color: var(--border-default, rgba(0, 255, 255, 0.2));
  --el-table-row-hover-bg-color: rgba(0, 255, 255, 0.05);
  --el-table-header-row-hover-bg-color: rgba(0, 255, 255, 0.05);
}

:deep(.el-table th.el-table__cell) {
  background: var(--bg-secondary, #0a0a0f) !important;
  color: var(--neon-cyan, #0ff) !important;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-weight: 600;
  letter-spacing: 1px;
}

:deep(.el-table td.el-table__cell) {
  background: var(--bg-panel, #0d0d14) !important;
  color: var(--text-primary, #e0e0e0) !important;
  border-color: var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(0, 255, 255, 0.05) !important;
}

:deep(.el-button--primary) {
  --el-button-bg-color: var(--neon-cyan, #0ff);
  --el-button-border-color: var(--neon-cyan, #0ff);
  --el-button-text-color: #000;
  background: var(--neon-cyan, #0ff);
  border-color: var(--neon-cyan, #0ff);
  color: #000;
}

:deep(.el-button--primary:hover) {
  background: var(--neon-cyan-light, #00f0ff);
  border-color: var(--neon-cyan-light, #00f0ff);
  color: #000;
}

:deep(.el-button--danger) {
  color: var(--neon-magenta, #f0f);
}
</style>