<template>
  <div class="quality-gate">
    <div class="page-header">
      <span class="page-title">质量门禁</span>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建门禁</el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="搜索门禁名称" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filterForm.gate_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="执行门禁" value="execution" />
            <el-option label="定时门禁" value="scheduled" />
            <el-option label="部署前门禁" value="pre_deploy" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.enabled" placeholder="全部" clearable style="width: 100px" @change="handleEnabledChange">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 门禁列表 -->
    <el-table
      v-loading="reportStore.loading"
      :data="reportStore.qualityGates"
      style="width: 100%"
      highlight-current-row
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="门禁名称" min-width="180">
        <template #default="{ row }">
          <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="gate_type" label="类型" width="120" align="center">
        <template #default="{ row }">
          <el-tag size="small">{{ formatGateType(row.gate_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="gate_level" label="等级" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getLevelType(row.gate_level)" size="small">{{ formatLevel(row.gate_level) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enabled" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.enabled"
            @change="handleToggleEnabled(row, $event)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="conditions" label="条件数" width="90" align="center">
        <template #default="{ row }">
          {{ row.conditions?.length ?? 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="last_result" label="最近结果" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.last_result" :type="getResultType(row.last_result)" size="small">
            {{ formatResult(row.last_result) }}
          </el-tag>
          <span v-else class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160" />
      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" text @click="handleEvaluate(row)">评估</el-button>
          <el-button type="primary" size="small" text @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" text @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="reportStore.gateTotal"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: var(--spacing-md)"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <!-- 评估结果弹窗 -->
    <el-dialog v-model="evalDialogVisible" title="门禁评估结果" width="560px">
      <el-descriptions v-if="evalResult" :column="1" border>
        <el-descriptions-item label="门禁名称">{{ evalResult.gate_name }}</el-descriptions-item>
        <el-descriptions-item label="门禁等级">
          <el-tag :type="getLevelType(evalResult.gate_level)">{{ formatLevel(evalResult.gate_level) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评估结果">
          <el-tag :type="getResultType(evalResult.overall_result)">
            {{ formatResult(evalResult.overall_result) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评估时间">{{ evalResult.evaluated_at }}</el-descriptions-item>
      </el-descriptions>
      <el-divider>条件详情</el-divider>
      <el-table v-if="evalResult?.details?.length" :data="evalResult.details" size="small">
        <el-table-column prop="metric" label="指标" />
        <el-table-column prop="operator" label="操作符" width="70" align="center" />
        <el-table-column prop="threshold" label="阈值" width="80" align="center" />
        <el-table-column prop="actual" label="实际值" width="80" align="center" />
        <el-table-column label="结果" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.result === 'pass' ? 'success' : 'danger'" size="small">
              {{ row.result === 'pass' ? '通过' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="说明" min-width="120" />
      </el-table>
      <el-empty v-else description="无详细结果" />
    </el-dialog>

    <!-- 新建/编辑门禁弹窗 -->
    <el-dialog
      v-model="formVisible"
      :title="isEdit ? '编辑门禁' : '新建门禁'"
      width="640px"
      :before-close="handleFormClose"
    >
      <el-form :model="gateForm" label-width="110px">
        <el-form-item label="门禁名称" required>
          <el-input v-model="gateForm.name" placeholder="请输入门禁名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="gateForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="门禁类型">
          <el-select v-model="gateForm.gate_type" style="width: 100%">
            <el-option label="执行门禁" value="execution" />
            <el-option label="定时门禁" value="scheduled" />
            <el-option label="部署前门禁" value="pre_deploy" />
          </el-select>
        </el-form-item>
        <el-form-item label="门禁等级">
          <el-radio-group v-model="gateForm.gate_level">
            <el-radio value="blocking">Blocking（阻断）</el-radio>
            <el-radio value="warning">Warning（警告）</el-radio>
            <el-radio value="info">Info（提示）</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 条件列表 -->
        <el-form-item label="门禁条件">
          <div class="conditions-wrapper">
            <div
              v-for="(cond, idx) in gateForm.conditions"
              :key="idx"
              class="condition-row"
            >
              <el-select v-model="cond.metric" placeholder="指标" style="width: 140px">
                <el-option label="通过率" value="pass_rate" />
                <el-option label="用例通过率" value="test_pass_rate" />
                <el-option label="缺陷数" value="defect_count" />
                <el-option label="严重缺陷数" value="critical_defects" />
                <el-option label="平均耗时" value="avg_duration" />
              </el-select>
              <el-select v-model="cond.operator" placeholder="操作符" style="width: 80px">
                <el-option label=">=" value=">=" />
                <el-option label="<=" value="<=" />
                <el-option label=">" value=">" />
                <el-option label="<" value="<" />
                <el-option label="==" value="==" />
                <el-option label="!=" value="!=" />
              </el-select>
              <el-input-number v-model="cond.threshold" :min="0" style="width: 100px" />
              <el-button type="danger" :icon="Delete" text @click="removeCondition(idx)">删除</el-button>
            </div>
            <el-button type="primary" text :icon="Plus" @click="addCondition">添加条件</el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleFormSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'

const reportStore = useReportStore()

const currentPage = ref(1)
const currentPageSize = ref(20)
const filterForm = ref({ keyword: '', gate_type: null, enabled: null })

const formVisible = ref(false)
const evalDialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const evalResult = ref(null)
const currentGate = ref(null)

const gateForm = ref({
  name: '',
  description: '',
  gate_type: 'execution',
  gate_level: 'warning',
  conditions: [],
})

onMounted(() => {
  loadGates()
})

function loadGates() {
  reportStore.fetchQualityGates({
    page: currentPage.value,
    page_size: currentPageSize.value,
  })
}

function handleFilter() {
  currentPage.value = 1
  reportStore.fetchQualityGates({
    page: 1,
    page_size: currentPageSize.value,
    ...filterForm.value,
  })
}

function handleReset() {
  filterForm.value = { keyword: '', gate_type: null, enabled: null }
  currentPage.value = 1
  loadGates()
}

function handleEnabledChange(val) {
  // Will be applied when filter is submitted
}

function handlePageChange(page) {
  currentPage.value = page
  reportStore.fetchQualityGates({
    page,
    page_size: currentPageSize.value,
    ...filterForm.value,
  })
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  reportStore.fetchQualityGates({ page: 1, page_size: size, ...filterForm.value })
}

function handleCreate() {
  isEdit.value = false
  gateForm.value = {
    name: '',
    description: '',
    gate_type: 'execution',
    gate_level: 'warning',
    conditions: [],
  }
  formVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  currentGate.value = row
  gateForm.value = {
    name: row.name || '',
    description: row.description || '',
    gate_type: row.gate_type || 'execution',
    gate_level: row.gate_level || 'warning',
    conditions: row.conditions ? row.conditions.map(c => ({ ...c })) : [],
  }
  formVisible.value = true
}

function handleFormClose() {
  formVisible.value = false
}

async function handleFormSubmit() {
  if (!gateForm.value.name.trim()) {
    ElMessage.warning('请输入门禁名称')
    return
  }

  saving.value = true
  try {
    const data = { ...gateForm.value }
    if (isEdit.value) {
      await reportStore.updateQualityGate(currentGate.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await reportStore.createQualityGate(data)
      ElMessage.success('创建成功')
    }
    formVisible.value = false
    loadGates()
  } catch {
    // error handled in store
  } finally {
    saving.value = false
  }
}

async function handleToggleEnabled(row, enabled) {
  try {
    await reportStore.updateQualityGate(row.id, { enabled })
    row.enabled = enabled
    ElMessage.success(enabled ? '已启用' : '已禁用')
  } catch {
    ElMessage.error('状态更新失败')
  }
}

async function handleEvaluate(row) {
  try {
    await ElMessageBox.confirm(
      '请在评估前确保已有所需的执行数据。是否继续？',
      '门禁评估',
      { confirmButtonText: '评估', cancelButtonText: '取消', type: 'info' }
    )
    const result = await reportStore.evaluateQualityGate(row.id, {
      scope_filter: { pass_rate: 95 },
    })
    evalResult.value = result
    evalDialogVisible.value = true
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('评估失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除门禁「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await reportStore.deleteQualityGate(row.id)
    ElMessage.success('删除成功')
    loadGates()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function addCondition() {
  gateForm.value.conditions.push({ metric: 'pass_rate', operator: '>=', threshold: 95 })
}

function removeCondition(idx) {
  gateForm.value.conditions.splice(idx, 1)
}

function formatGateType(type) {
  const map = { execution: '执行', scheduled: '定时', pre_deploy: '部署前' }
  return map[type] || type
}

function formatLevel(level) {
  const map = { blocking: '阻断', warning: '警告', info: '提示' }
  return map[level] || level
}

function getLevelType(level) {
  const map = { blocking: 'danger', warning: 'warning', info: 'info' }
  return map[level] || 'info'
}

function formatResult(result) {
  const map = { pass: '通过', fail: '失败', warning: '警告', skipped: '跳过' }
  return map[result] || result
}

function getResultType(result) {
  const map = { pass: 'success', fail: 'danger', warning: 'warning', skipped: 'info' }
  return map[result] || 'info'
}
</script>

<style scoped>
.quality-gate {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-card {
  border-radius: var(--border-radius-base);
}

.text-muted {
  color: var(--text-disabled);
  font-size: 13px;
}

.conditions-wrapper {
  width: 100%;
}

.condition-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}
</style>
