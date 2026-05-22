<template>
  <div class="quality-gate-page">
    <!-- 页面标题区 -->
    <header class="quality-gate-page__header">
      <div>
        <h1>质量门禁</h1>
        <p>配置质量门槛，自动拦截不达标的发布。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="handleCreate">
        新建门禁
      </el-button>
    </header>

    <!-- 查询区 -->
    <section class="quality-gate-page__filters">
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="关键词：" class="filter-item filter-item--keyword">
            <el-input
              v-model="draftFilters.keyword"
              placeholder="搜索门禁名称"
              clearable
              class="search-bar__input"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="门禁类型：" class="filter-item filter-item--type">
            <el-select
              v-model="draftFilters.gate_type"
              placeholder="全部类型"
              clearable
              class="filter-control"
            >
              <el-option label="执行门禁" value="execution" />
              <el-option label="定时门禁" value="scheduled" />
              <el-option label="部署前门禁" value="pre_deploy" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态：" class="filter-item filter-item--status">
            <el-select
              v-model="draftFilters.enabled"
              placeholder="全部状态"
              clearable
              class="filter-control"
            >
              <el-option label="启用" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <!-- 门禁列表 -->
    <section class="quality-gate-page__table">
      <el-table
        v-loading="reportStore.loading"
        :data="reportStore.qualityGates"
        height="100%"
        highlight-current-row
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="门禁名称" min-width="180">
          <template #default="{ row }">
            <span class="name-cell">{{ row.name }}</span>
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
            <el-button type="primary" text size="small" @click="handleEvaluate(row)">评估</el-button>
            <el-button type="primary" text size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的门禁</span>
        </template>
      </el-table>

      <div class="quality-gate-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="reportStore.gateTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

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
import { ref, onMounted } from 'vue'
import { Plus, Search, RefreshLeft, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'

const reportStore = useReportStore()

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const draftFilters = ref({
  keyword: '',
  gate_type: null,
  enabled: null,
})

const appliedFilters = ref({
  keyword: '',
  gate_type: null,
  enabled: null,
})

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
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...buildQueryParams(),
  })
}

function buildQueryParams() {
  const params = {}
  if (appliedFilters.value.keyword) params.keyword = appliedFilters.value.keyword
  if (appliedFilters.value.gate_type) params.gate_type = appliedFilters.value.gate_type
  if (appliedFilters.value.enabled !== null) params.enabled = appliedFilters.value.enabled
  return params
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  loadGates()
}

function handleReset() {
  draftFilters.value = { keyword: '', gate_type: null, enabled: null }
  appliedFilters.value = { keyword: '', gate_type: null, enabled: null }
  pagination.value.page = 1
  loadGates()
}

function handlePageChange(page) {
  pagination.value.page = page
  loadGates()
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadGates()
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
/* ── 页面容器 ── */
.quality-gate-page {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
}

.quality-gate-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: quality-gate-scan 14s linear infinite;
}

.quality-gate-page::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: quality-gate-particles 18s ease-in-out infinite alternate;
}

@keyframes quality-gate-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes quality-gate-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes quality-gate-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes quality-gate-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

@media (prefers-reduced-motion: reduce) {
  .quality-gate-page::before,
  .quality-gate-page::after {
    animation: none;
  }
}

/* ── 标题区 ── */
.quality-gate-page__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
  z-index: 1;
}

.quality-gate-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .quality-gate-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

.quality-gate-page__header h1,
.quality-gate-page__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

.quality-gate-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.quality-gate-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.btn-primary-add {
  position: relative;
  z-index: 1;
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
}

/* ── 查询区 ── */
.quality-gate-page__filters {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 26px 26px, 26px 26px, auto, auto;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.quality-gate-page__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: quality-gate-form-scan 12s linear infinite;
}

html:not(.dark) .quality-gate-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .quality-gate-page__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%);
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
}

.filter-form__row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  width: 100%;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.filter-item {
  display: flex;
  flex: 0 0 auto;
  align-items: flex-end;
}

.filter-control {
  width: 180px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  margin-left: auto;
}

.filter-actions :deep(.el-button),
.filter-actions .el-button {
  min-width: 76px;
  height: 34px;
  margin-left: 0;
}

.search-bar__input {
  width: 280px;
}

/* ── 表格区 ── */
.quality-gate-page__table {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 32px 32px, 32px 32px, auto, auto;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.quality-gate-page__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: quality-gate-table-scan 12s linear infinite;
}

html:not(.dark) .quality-gate-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

.quality-gate-page__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  position: relative;
  z-index: 1;
}

html:not(.dark) .quality-gate-page__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
}

.quality-gate-page__table :deep(.el-table__inner-wrapper::before) {
  background: rgba(56, 189, 248, 0.12);
}

.quality-gate-page__table :deep(.el-table__body-wrapper),
.quality-gate-page__table :deep(.el-table__header-wrapper),
.quality-gate-page__table :deep(.el-scrollbar__view) {
  background: transparent;
}

.quality-gate-page__table :deep(.el-table__header th) {
  height: 44px;
  color: var(--text-secondary);
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  font-weight: 700;
  font-size: 13px;
}

.quality-gate-page__table :deep(.el-table__body td) {
  height: 48px;
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.quality-gate-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .quality-gate-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.quality-gate-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.quality-gate-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right),
.quality-gate-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.quality-gate-page__table :deep(.el-table .cell) {
  padding: 0 10px;
}

.quality-gate-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

@media (prefers-reduced-motion: reduce) {
  .quality-gate-page__table::before {
    animation: none;
  }
}

.name-cell {
  font-weight: 600;
  color: var(--text-primary);
}

.text-muted {
  color: var(--text-disabled);
  font-size: 13px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 分页 ── */
.quality-gate-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .quality-gate-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

/* ── 弹窗条件列表 ── */
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
