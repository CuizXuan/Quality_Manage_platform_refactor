<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <div>
          <span class="section-kicker">{{ kicker }}</span>
        </div>
        <el-button type="primary" @click="openCreate">{{ createLabel }}</el-button>
      </div>

      <el-table :data="items" border stripe class="crud-table">
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
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
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
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="editing" :title="`${form.id ? '编辑' : '新建'}${title}`" size="420px">
      <el-form :model="form" label-position="top" class="drawer-form" @submit.prevent>
        <el-form-item v-for="field in editableFields" :key="field.key" :label="field.label" :required="field.required">
          <el-select v-if="field.type === 'select'" v-model="form[field.key]" class="form-control">
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
            class="form-control"
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
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  kicker: { type: String, required: true },
  createLabel: { type: String, required: true },
  items: { type: Array, required: true },
  fields: { type: Array, required: true },
  actions: { type: Array, default: () => [] },
})

const emit = defineEmits(['create', 'update', 'remove', 'action'])
const editing = ref(false)
const form = reactive({})
const visibleFields = computed(() => props.fields.filter((field) => !field.hidden).slice(0, 5))
const editableFields = computed(() => props.fields.filter((field) => !field.readonly))

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
</script>

<style scoped>
.crud-table {
  width: 100%;
}

.drawer-form {
  padding-right: var(--spacing-sm);
}

.form-control {
  width: 100%;
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
</style>
