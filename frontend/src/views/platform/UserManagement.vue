<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <div>
          <span class="section-kicker">Users</span>
          <h2>用户管理</h2>
        </div>
        <button class="primary-btn" type="button" @click="openCreate">新建用户</button>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>姓名</th>
            <th>邮箱</th>
            <th>组织</th>
            <th>角色</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in users" :key="item.id">
            <td>{{ item.username }}</td>
            <td>{{ item.display_name || '-' }}</td>
            <td>{{ item.email }}</td>
            <td>{{ item.organization_name || '-' }}</td>
            <td>{{ item.roles.join(', ') || '-' }}</td>
            <td><span class="status-pill" :class="item.status">{{ item.status }}</span></td>
            <td class="row-actions">
              <button type="button" @click="openEdit(item)">编辑</button>
              <button type="button" @click="removeUser(item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="editing" class="drawer-mask" @click.self="closeEditor">
      <form class="editor-drawer" @submit.prevent="saveUser">
        <h3>{{ form.id ? '编辑用户' : '新建用户' }}</h3>
        <label>用户名<input v-model="form.username" :disabled="!!form.id" required /></label>
        <label>姓名<input v-model="form.display_name" /></label>
        <label>邮箱<input v-model="form.email" required /></label>
        <label v-if="!form.id">密码<input v-model="form.password" type="password" required /></label>
        <label>手机号<input v-model="form.phone" /></label>
        <label>组织
          <select v-model.number="form.organization_id">
            <option :value="null">未分配</option>
            <option v-for="org in organizations" :key="org.id" :value="org.id">{{ org.name }}</option>
          </select>
        </label>
        <label>状态
          <select v-model="form.status">
            <option value="active">active</option>
            <option value="disabled">disabled</option>
          </select>
        </label>
        <div class="check-grid">
          <label v-for="role in roles" :key="role.id" class="check-item">
            <input v-model="form.role_ids" type="checkbox" :value="role.id" />
            {{ role.name }}
          </label>
        </div>
        <div class="drawer-actions">
          <button type="button" @click="closeEditor">取消</button>
          <button class="primary-btn" type="submit">保存</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { systemApi } from '@/api/system'

const users = ref([])
const roles = ref([])
const organizations = ref([])
const editing = ref(false)
const form = reactive(defaultForm())

function defaultForm() {
  return {
    id: null,
    username: '',
    display_name: '',
    email: '',
    password: '',
    phone: '',
    organization_id: null,
    status: 'active',
    role_ids: [],
  }
}

async function loadData() {
  const [userRes, roleRes, orgRes] = await Promise.all([
    systemApi.users.list(),
    systemApi.roles.list(),
    systemApi.organizations.list(),
  ])
  users.value = userRes.data
  roles.value = roleRes.data
  organizations.value = orgRes.data
}

function resetForm(data = defaultForm()) {
  Object.assign(form, defaultForm(), data)
}

function openCreate() {
  resetForm()
  editing.value = true
}

function openEdit(user) {
  resetForm({ ...user, password: '', role_ids: [...user.role_ids] })
  editing.value = true
}

function closeEditor() {
  editing.value = false
}

async function saveUser() {
  const payload = { ...form }
  if (payload.id) {
    delete payload.username
    delete payload.password
    await systemApi.users.update(payload.id, payload)
  } else {
    await systemApi.users.create(payload)
  }
  editing.value = false
  await loadData()
}

async function removeUser(user) {
  await systemApi.users.delete(user.id)
  await loadData()
}

onMounted(loadData)
</script>

