<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <span class="section-label">{{ title }}</span>
        <el-button type="primary" @click="openCreate">{{ createLabel }}</el-button>
      </div>

      <div v-if="showSearch" class="toolbar">
        <el-input
          v-model="queryKeyword"
          placeholder="搜索关键词"
          prefix-icon="Search"
          clearable
          style="width: 240px"
          @input="onQueryChange"
        />
        <slot name="search" />
      </div>

      <el-table :data="pagedItems" border class="data-table" v-loading="loading">
        <el-table-column
          v-for="field in visibleFields"
          :key="field.key"
          :prop="field.key"
          :label="field.label"
          min-width="140"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <el-tag v-if="field.key === 'status'" :type="row[field.key] === 'active' ? 'success' : 'info'" effect="light">
              {{ formatValue(row[field.key], field) }}
            </el-tag>
            <span v-else-if="field.key === 'permissions'" class="summary-pill">
              {{ formatValue(row[field.key], field) }}
            </span>
            <span v-else>{{ formatValue(row[field.key], field) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" :width="actionColWidth" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button
                v-for="action in actions"
                :key="action.key"
                size="small"
                text
                type="primary"
                @click="$emit('action', { action, item: row })"
              >
                {{ action.label }}
              </el-button>
              <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click="$emit('remove', row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[15, 30, 50]"
          layout="total, sizes, prev, pager, next"
          background
        />
      </div>
    </section>

    <el-dialog v-model="editing" :title="`${form.id ? '编辑' : '新建'}${title}`" top="4vh" width="min(480px, 92vw)" destroy-on-close append-to-body>
      <el-form :model="form" label-position="top" class="drawer-form" @submit.prevent>
        <el-form-item v-for="field in editableFields" :key="field.key" :label="field.label" :required="field.required">
          <el-select v-if="field.type === 'select'" v-model="form[field.key]" class="full-width">
            <el-option
              v-for="option in field.options"
              :key="optionValue(option)"
              :label="optionLabel(option)"
              :value="optionValue(option)"
            />
          </el-select>

          <el-checkbox-group v-else-if="field.type === 'checks'" v-model="form[field.key]" class="check-group">
            <el-checkbox v-for="option in field.options" :key="option.value" :label="option.value">
              {{ option.label }}
            </el-checkbox>
          </el-checkbox-group>

          <el-radio-group v-else-if="field.type === 'icon'" v-model="form[field.key]" class="icon-radio-group">
            <el-radio-button v-for="option in field.options" :key="option.value" :label="option.value">
              <span class="icon-option">{{ option.symbol }}</span>
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>

          <el-input-number
            v-else-if="field.type === 'number'"
            v-model="form[field.key]"
            class="full-width"
            :min="field.min"
            :max="field.max"
          />

          <el-input
            v-else
            v-model="form[field.key]"
            :disabled="!!form.id && field.createOnly"
            :type="field.type === 'password' ? 'password' : 'text'"
            :show-password="field.type === 'password'"
            :placeholder="field.placeholder || ''"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="editing = false">取消</el-button>
          <el-button type="primary" @click="submit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  kicker: { type: String, required: true },
  createLabel: { type: String, required: true },
  items: { type: Array, required: true },
  fields: { type: Array, required: true },
  actions: { type: Array, default: () => [] },
  actionColWidth: { type: Number, default: 220 },
  showSearch: { type: Boolean, default: true },
})

const emit = defineEmits(['create', 'update', 'remove', 'action', 'query'])

const loading = ref(false)
const editing = ref(false)
const form = reactive({})
const queryKeyword = ref('')
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)

const visibleFields = computed(() => props.fields.filter((field) => !field.hidden).slice(0, 5))
const editableFields = computed(() => props.fields.filter((field) => !field.readonly))
const pagedItems = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return props.items.slice(start, start + pageSize.value)
})

function openCreate() {
  resetForm()
  editing.value = true
}

function openEdit(item) {
  resetForm(item)
  editing.value = true
}

function resetForm(item = {}) {
  for (const key of Object.keys(form)) delete form[key]
  Object.assign(form, { status: 'active', sort_order: 0 }, cloneItem(item))
  for (const field of props.fields) {
    if (field.type === 'checks' && !Array.isArray(form[field.key])) form[field.key] = []
  }
}

function submit() {
  emit(form.id ? 'update' : 'create', { ...form })
  editing.value = false
}

function formatValue(value, field) {
  if (field?.formatter) return field.formatter(value)
  if (field?.type === 'select') {
    return optionLabel(field.options.find((item) => optionValue(item) === value))
  }
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'boolean') return value ? '是' : '否'
  return value ?? '-'
}

function optionValue(option) {
  return typeof option === 'object' ? option.value : option
}

function optionLabel(option) {
  if (!option) return '-'
  return typeof option === 'object' ? option.label : option
}

function cloneItem(item) {
  return Object.fromEntries(
    Object.entries(item).map(([key, value]) => [key, Array.isArray(value) ? [...value] : value]),
  )
}

let queryTimer = null
function onQueryChange() {
  clearTimeout(queryTimer)
  queryTimer = setTimeout(() => {
    page.value = 1
    emit('query', { keyword: queryKeyword.value, page: page.value, page_size: pageSize.value })
  }, 300)
}

function setItems(items) {
  total.value = items.length || 0
}

defineExpose({ setItems })

watch(page, () => emit('query', { keyword: queryKeyword.value, page: page.value, page_size: pageSize.value }))
watch(pageSize, () => { page.value = 1; emit('query', { keyword: queryKeyword.value, page: page.value, page_size: pageSize.value }) })
</script>

<style scoped>
.full-width {
  width: 100%;
}

.drawer-form {
  padding-right: var(--spacing-sm);
}

.check-group {
  display: grid;
  gap: var(--spacing-sm);
}

.icon-radio-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.icon-radio-group :deep(.el-radio-button__inner) {
  width: 100%;
  text-align: left;
}

.icon-option {
  margin-right: var(--spacing-xs);
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
}
</style>
