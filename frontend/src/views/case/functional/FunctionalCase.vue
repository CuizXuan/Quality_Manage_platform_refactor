<template>
  <div class="case-page">
    <aside class="case-sidebar">
      <CaseSidebar @folder-selected="handleFolderSelected" />
    </aside>
    <main class="case-list">
      <CaseList ref="caseListRef" :case-type="caseType" :folder-id="currentFolderId" @case-selected="handleCaseSelected" @create-case="handleCreateCase" />
    </main>
    <aside class="case-detail">
      <CaseDetail v-if="selectedCase" :case-data="selectedCase" @saved="handleSaved" />
    </aside>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseSidebar from '../CaseSidebar.vue'
import CaseList from '../CaseList.vue'
import CaseDetail from '../CaseDetail.vue'

const caseType = ref('functional')
const currentFolderId = ref(null)
const selectedCase = ref(null)
const caseListRef = ref(null)

function handleFolderSelected(folderId) {
  currentFolderId.value = folderId
}

function handleCaseSelected(caseItem) {
  selectedCase.value = caseItem
}

function handleCreateCase() {
  // 打开创建用例对话框
}

function handleSaved() {
  caseListRef.value?.reload()
}
</script>

<style scoped>
.case-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.case-sidebar {
  width: 240px;
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.case-list {
  flex: 1;
  min-width: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.case-detail {
  width: 400px;
  border-left: 1px solid var(--border-color);
  overflow-y: auto;
}
</style>