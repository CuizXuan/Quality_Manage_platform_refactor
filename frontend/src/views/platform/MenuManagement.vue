<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <span class="section-kicker">Menus 菜单</span>
        <button class="primary-btn" type="button" @click="openCreate()">新建菜单</button>
      </div>

      <table class="data-table tree-table">
        <thead>
          <tr>
            <th>菜单名称</th>
            <th>路径</th>
            <th>图标</th>
            <th>组件</th>
            <th>权限编码</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in visibleMenus" :key="item.id">
            <td>
              <div class="tree-cell" :style="{ paddingLeft: `${item.level * 22}px` }">
                <button
                  v-if="item.children.length"
                  class="tree-toggle"
                  type="button"
                  @click="toggleMenu(item.id)"
                >
                  {{ collapsedIds.has(item.id) ? '›' : '⌄' }}
                </button>
                <span v-else class="tree-toggle-placeholder"></span>
                <span class="truncate-cell" :title="item.name">{{ item.name }}</span>
              </div>
            </td>
            <td><span class="truncate-cell" :title="item.path">{{ item.path || '-' }}</span></td>
            <td><span class="truncate-cell" :title="formatMenuIcon(item.icon)">{{ formatMenuIcon(item.icon) }}</span></td>
            <td><span class="truncate-cell" :title="item.component">{{ item.component || '-' }}</span></td>
            <td><span class="truncate-cell" :title="item.permission_code">{{ item.permission_code || '-' }}</span></td>
            <td><span class="status-pill" :class="item.status">{{ formatStatus(item.status) }}</span></td>
            <td class="row-actions">
              <button type="button" @click="openCreate(item)">新增子级</button>
              <button type="button" @click="openEdit(item)">编辑</button>
              <button type="button" @click="removeMenu(item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="editing" class="drawer-mask" @click.self="closeEditor">
      <form class="editor-drawer" @submit.prevent="saveMenu">
        <h3>{{ form.id ? '编辑菜单' : '新建菜单' }}</h3>
        <label>上级菜单
          <select v-model.number="form.parent_id">
            <option :value="null">一级菜单</option>
            <option v-for="item in parentOptions" :key="item.id" :value="item.id">
              {{ '　'.repeat(item.level) }}{{ item.name }}
            </option>
          </select>
        </label>
        <label>菜单名称<input v-model="form.name" required /></label>
        <label>菜单编码<input v-model="form.code" :disabled="!!form.id" required /></label>
        <label>路径<input v-model="form.path" /></label>
        <label>菜单图标
          <div class="icon-grid">
            <label v-for="option in menuIconOptions" :key="option.value" class="icon-item">
              <input v-model="form.icon" type="radio" :value="option.value" />
              <span>{{ option.symbol }}</span>
              {{ option.label }}
            </label>
          </div>
        </label>
        <label>组件标识<input v-model="form.component" /></label>
        <label>权限编码<input v-model="form.permission_code" /></label>
        <label>状态
          <select v-model="form.status">
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label>排序<input v-model.number="form.sort_order" type="number" /></label>
        <div class="drawer-actions">
          <button type="button" @click="closeEditor">取消</button>
          <button class="primary-btn" type="submit">保存</button>
        </div>
      </form>
    </div>
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
