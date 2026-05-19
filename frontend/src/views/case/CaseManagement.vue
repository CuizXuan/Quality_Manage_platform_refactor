<template>
  <div class="case-management">
    <el-container>
      <el-aside width="240px" class="case-sidebar">
        <CaseSidebar @folder-selected="handleFolderSelected" />
      </el-aside>
      <el-main class="case-list">
        <CaseList
          ref="caseListRef"
          :folder-id="currentFolderId"
          @case-selected="handleCaseSelected"
          @create-case="handleCreateCase"
        />
      </el-main>
      <el-aside width="480px" class="case-detail">
        <CaseDetail
          v-if="currentCase"
          :case-data="currentCase"
          @saved="handleSaved"
          @deleted="handleDeleted"
        />
        <div v-else class="case-detail-empty">
          <el-empty description="请选择用例或新建用例" />
        </div>
      </el-aside>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseSidebar from './CaseSidebar.vue'
import CaseList from './CaseList.vue'
import CaseDetail from './CaseDetail.vue'

const currentFolderId = ref(null)
const currentCase = ref(null)
const caseListRef = ref(null)

function handleFolderSelected(folderId) {
  currentFolderId.value = folderId
}

function handleCaseSelected(caseItem) {
  currentCase.value = caseItem
}

function handleCreateCase() {
  currentCase.value = { id: null, isNew: true }
}

function handleSaved() {
  caseListRef.value?.reload()
}

function handleDeleted() {
  currentCase.value = null
  caseListRef.value?.reload()
}
</script>

<style scoped>
.case-management {
  height: 100%;
  background: var(--bg-page);
}

.case-sidebar {
  background: var(--bg-container);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.case-list {
  background: var(--bg-page);
  padding: 0;
  overflow-y: auto;
}

.case-detail {
  background: var(--bg-container);
  border-left: 1px solid var(--border-color);
  overflow-y: auto;
}

.case-detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>