<template>
  <el-dialog v-model="visible" title="个人中心" width="480px" destroy-on-close>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本信息" name="info">
        <el-descriptions :column="1" border label-width="100px" class="info-descriptions">
          <el-descriptions-item label="用户名">{{ userInfo.username }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ userInfo.nickname || '—' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ userInfo.phone || '—' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ userInfo.email || '—' }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ userInfo.role_name || '—' }}</el-descriptions-item>
          <el-descriptions-item label="组织">{{ userInfo.org_name || '—' }}</el-descriptions-item>
          <el-descriptions-item label="最后登录">
            {{ userInfo.last_login_at ? formatTime(userInfo.last_login_at) : '—' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <el-tab-pane label="修改密码" name="password">
        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
          <el-form-item label="当前密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
          </el-form-item>
        </el-form>
        <div class="dialog-footer">
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleChangePassword">保存</el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import feedback from '@/utils/feedback'

const authStore = useAuthStore()

const visible = ref(false)
const activeTab = ref('info')
const saving = ref(false)
const passwordFormRef = ref(null)

const userInfo = computed(() => ({
  username: authStore.user?.username || '—',
  nickname: authStore.user?.nickname,
  phone: authStore.user?.phone,
  email: authStore.user?.email,
  role_name: authStore.user?.role_name,
  org_name: authStore.user?.org_name,
  last_login_at: authStore.user?.last_login_at,
}))

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

function formatTime(timeStr) {
  if (!timeStr) return '—'
  const d = new Date(timeStr)
  if (isNaN(d.getTime())) return timeStr
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await authStore.changePassword(passwordForm.old_password, passwordForm.new_password)
      feedback.success('密码修改成功')
      visible.value = false
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
    } catch (err) {
      feedback.error(err.message || '密码修改失败')
    } finally {
      saving.value = false
    }
  })
}

function open() {
  activeTab.value = 'info'
  visible.value = true
}

defineExpose({ open })
</script>

<style scoped>
.info-descriptions {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
</style>
