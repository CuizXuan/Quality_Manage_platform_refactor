<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <div>
          <span class="section-kicker">{{ kicker }}</span>
        </div>
        <button class="primary-btn" type="button" @click="openCreate">{{ createLabel }}</button>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th v-for="field in visibleFields" :key="field.key">{{ field.label }}</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td v-for="field in visibleFields" :key="field.key">
              <span :class="cellClass(field)" :title="formatValue(item[field.key], field)">
                {{ formatValue(item[field.key], field) }}
              </span>
            </td>
            <td class="row-actions">
              <button
                v-for="action in actions"
                :key="action.key"
                type="button"
                @click="$emit('action', { action, item })"
              >
                {{ action.label }}
              </button>
              <button type="button" @click="openEdit(item)">编辑</button>
              <button type="button" @click="$emit('remove', item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="editing" class="drawer-mask" @click.self="editing = false">
      <form class="editor-drawer" @submit.prevent="submit">
        <h3>{{ form.id ? '编辑' : '新建' }}{{ title }}</h3>
        <label v-for="field in editableFields" :key="field.key">
          {{ field.label }}
          <select v-if="field.type === 'select'" v-model="form[field.key]">
            <option v-for="option in field.options" :key="optionValue(option)" :value="optionValue(option)">
              {{ optionLabel(option) }}
            </option>
          </select>
          <div v-else-if="field.type === 'checks'" class="check-grid">
            <label v-for="option in field.options" :key="option.value" class="check-item">
              <input v-model="form[field.key]" type="checkbox" :value="option.value" />
              {{ option.label }}
            </label>
          </div>
          <div v-else-if="field.type === 'icon'" class="icon-grid">
            <label v-for="option in field.options" :key="option.value" class="icon-item">
              <input v-model="form[field.key]" type="radio" :value="option.value" />
              <span>{{ option.symbol }}</span>
              {{ option.label }}
            </label>
          </div>
          <input
            v-else
            v-model="form[field.key]"
            :disabled="!!form.id && field.createOnly"
            :required="field.required"
            :type="field.type || 'text'"
            :placeholder="field.placeholder || ''"
          />
        </label>
        <div class="drawer-actions">
          <button type="button" @click="editing = false">取消</button>
          <button class="primary-btn" type="submit">保存</button>
        </div>
      </form>
    </div>
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

function cellClass(field) {
  return field.key === 'permissions' ? 'summary-pill' : 'truncate-cell'
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
