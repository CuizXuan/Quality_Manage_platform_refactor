<template>
  <div class="execution-detail-page scenario-workbench-page">
    <header class="execution-detail-page__header scenario-workbench-page__header">
      <div>
        <h1>执行详情</h1>
        <p>查看统一执行记录、步骤日志与执行产物。</p>
      </div>
    </header>

    <section class="execution-detail-page__summary scenario-workbench-page__panel" v-if="executionStore.currentRun">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="Run ID">{{ executionStore.currentRun.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ executionStore.currentRun.status }}</el-descriptions-item>
        <el-descriptions-item label="队列状态">{{ executionStore.currentRun.queue_status }}</el-descriptions-item>
        <el-descriptions-item label="执行对象">{{ executionStore.currentRun.target_type }} #{{ executionStore.currentRun.target_id }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ executionStore.currentRun.duration_ms || 0 }} ms</el-descriptions-item>
        <el-descriptions-item label="来源执行">{{ executionStore.currentRun.source_run_id || '—' }}</el-descriptions-item>
      </el-descriptions>
    </section>

    <section class="execution-detail-page__table scenario-workbench-page__panel">
      <el-table :data="executionStore.currentRun?.items || []" height="100%">
        <el-table-column prop="item_type" label="项目类型" width="100" />
        <el-table-column prop="item_name" label="项目名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="步骤日志" min-width="340">
          <template #default="{ row }">
            <div v-if="row.step_logs?.length" class="step-log-list">
              <div v-for="log in row.step_logs" :key="log.id" class="step-log-item">
                <strong>{{ log.step_name }}</strong>
                <span>{{ log.status }}</span>
                <span v-if="log.error_message">{{ log.error_message }}</span>
              </div>
            </div>
            <span v-else class="text-muted">暂无日志</span>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useExecutionStore } from '@/stores/executionStore'

const route = useRoute()
const executionStore = useExecutionStore()

onMounted(async () => {
  await executionStore.fetchRun(route.params.id)
  await executionStore.fetchArtifacts(route.params.id)
})
</script>

<style scoped>
.execution-detail-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
}

.execution-detail-page__header {
  min-height: 56px;
  padding: 12px 16px;
}

.execution-detail-page__header h1,
.execution-detail-page__header p {
  margin: 0;
}

.execution-detail-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
}

.execution-detail-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.execution-detail-page__summary {
  padding: 14px;
}

.execution-detail-page__table {
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
}

.step-log-list {
  display: grid;
  gap: 6px;
}

.step-log-item {
  display: grid;
  gap: 2px;
}

.text-muted {
  color: var(--text-secondary);
}
</style>
