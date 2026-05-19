<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <span class="section-kicker">Menus 菜单</span>
        <el-button type="primary" @click="openCreate()">新建菜单</el-button>
      </div>

      <el-table :data="visibleMenus" row-key="id" border stripe class="menu-table">
        <el-table-column label="菜单名称" min-width="220">
          <template #default="{ row }">
            <div class="tree-cell" :style="{ paddingLeft: `${row.level * 22}px` }">
              <el-button
                v-if="row.children.length"
                text
                size="small"
                class="tree-toggle"
                @click.stop="toggleMenu(row.id)"
              >
                {{ collapsedIds.has(row.id) ? '›' : '⌄' }}
              </el-button>
              <span v-else class="tree-toggle-placeholder"></span>
              <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.path || '-' }}</template>
        </el-table-column>
        <el-table-column label="图标" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ formatMenuIcon(row.icon) }}</template>
        </el-table-column>
        <el-table-column prop="component" label="组件" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.component || '-' }}</template>
        </el-table-column>
        <el-table-column prop="permission_code" label="权限编码" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.permission_code || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="light">
              {{ formatStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openCreate(row)">新增子级</el-button>
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" text type="danger" @click="removeMenu(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="editing" :title="form.id ? '编辑菜单' : '新建菜单'" size="420px">
      <el-form :model="form" label-position="top">
        <el-form-item label="上级菜单">
          <el-select v-model="form.parent_id" class="form-control">
            <el-option :value="null" label="一级菜单" />
            <el-option
              v-for="item in parentOptions"
              :key="item.id"
              :label="`${'　'.repeat(item.level)}${item.name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="菜单名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="菜单编码" required>
          <el-input v-model="form.code" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="路径">
          <el-input v-model="form.path" />
        </el-form-item>
        <el-form-item label="菜单图标">
          <el-radio-group v-model="form.icon" class="icon-radio-group">
            <el-radio-button v-for="option in menuIconOptions" :key="option.value" :label="option.value">
              <span class="icon-option">{{ option.symbol }}</span>
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="组件标识">
          <el-input v-model="form.component" />
        </el-form-item>
        <el-form-item label="权限编码">
          <el-input v-model="form.permission_code" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" class="form-control">
            <el-option v-for="option in statusOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" class="form-control" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="closeEditor">取消</el-button>
          <el-button type="primary" @click="saveMenu">保存</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { systemApi } from '@/api/system'
import { formatMenuIcon, menuIconOptions } from './menuIconLibrary'
import { formatStatus, statusOptions } from './statusOptions'

const menus = ref([])
const editing = ref(false)
const collapsedIds = ref(new Set())
const form = reactive(defaultForm())

const menuTree = computed(() => buildMenuTree(menus.value))
const visibleMenus = computed(() => flattenMenus(menuTree.value))
const parentOptions = computed(() => {
  const blockedIds = getDescendantIds(form.id, menuTree.value)
  return visibleMenus.value.filter((item) => item.id !== form.id && !blockedIds.has(item.id))
})

function defaultForm() {
  return {
    id: null,
    parent_id: null,
    name: '',
    code: '',
    path: '',
    icon: 'PanelLeft',
    component: '',
    permission_code: '',
    status: 'active',
    sort_order: 0,
  }
}

async function loadMenus() {
  const response = await systemApi.menus.list()
  menus.value = response.data
}

function openCreate(parent = null) {
  resetForm({ parent_id: parent?.id || null })
  editing.value = true
}

function openEdit(item) {
  resetForm(item)
  editing.value = true
}

function closeEditor() {
  editing.value = false
}

async function saveMenu() {
  const payload = { ...form }
  if (payload.id) {
    await systemApi.menus.update(payload.id, payload)
  } else {
    delete payload.id
    await systemApi.menus.create(payload)
  }
  closeEditor()
  await loadMenus()
}

async function removeMenu(item) {
  await systemApi.menus.delete(item.id)
  await loadMenus()
}

function resetForm(data = {}) {
  Object.assign(form, defaultForm(), data)
}

function toggleMenu(id) {
  const next = new Set(collapsedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  collapsedIds.value = next
}

function buildMenuTree(items) {
  const nodes = items.map((item) => ({ ...item, children: [], level: 0 }))
  const nodeMap = new Map(nodes.map((item) => [item.id, item]))
  const roots = []
  for (const node of nodes) {
    const parent = nodeMap.get(node.parent_id)
    if (parent) {
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  }
  return sortMenus(roots)
}

function sortMenus(items) {
  return items
    .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
    .map((item) => ({ ...item, children: sortMenus(item.children) }))
}

function flattenMenus(items, level = 0) {
  return items.flatMap((item) => {
    const current = { ...item, level }
    if (collapsedIds.value.has(item.id)) return [current]
    return [current, ...flattenMenus(item.children, level + 1)]
  })
}

function getDescendantIds(id, items) {
  const found = findMenu(id, items)
  return new Set(found ? flattenAll(found.children).map((item) => item.id) : [])
}

function findMenu(id, items) {
  for (const item of items) {
    if (item.id === id) return item
    const found = findMenu(id, item.children)
    if (found) return found
  }
  return null
}

function flattenAll(items) {
  return items.flatMap((item) => [item, ...flattenAll(item.children)])
}

onMounted(loadMenus)
</script>

<style scoped>
.menu-table,
.form-control {
  width: 100%;
}

.tree-cell {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  min-width: 0;
}

.tree-toggle,
.tree-toggle-placeholder {
  width: 26px;
  flex: 0 0 26px;
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
