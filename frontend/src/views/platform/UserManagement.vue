<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-head">
        <div>
          <span class="section-kicker">Users</span>
        </div>
        <el-button type="primary" @click="openCreate">新建用户</el-button>
      </div>

      <el-table :data="users" border stripe class="user-table">
        <el-table-column prop="username" label="用户名" min-width="130" show-overflow-tooltip />
        <el-table-column prop="display_name" label="姓名" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.display_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="organization_name" label="组织" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.organization_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.roles.join('，') || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="light">
              {{ formatStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" text type="danger" @click="removeUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="editing" :title="form.id ? '编辑用户' : '新建用户'" size="420px">
      <el-form :model="form" label-position="top">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="密码" required>
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="组织">
          <el-select v-model="form.organization_id" class="form-control">
            <el-option :value="null" label="未分配" />
            <el-option v-for="org in organizations" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" class="form-control">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-checkbox-group v-model="form.role_ids" class="role-checks">
            <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">
              {{ role.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="closeEditor">取消</el-button>
          <el-button type="primary" @click="saveUser">保存</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { systemApi } from '@/api/system'
import { formatStatus } from './statusOptions'

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

<style scoped>
.user-table,
.form-control {
  width: 100%;
}

.role-checks {
  display: grid;
  gap: var(--spacing-sm);
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
