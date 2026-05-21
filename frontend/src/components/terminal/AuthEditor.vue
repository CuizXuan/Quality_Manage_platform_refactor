<template>
  <div class="auth-editor">
    <el-radio-group v-model="localAuthType" class="auth-type-select">
      <el-radio label="none">无</el-radio>
      <el-radio label="bearer">Bearer Token</el-radio>
      <el-radio label="basic">Basic Auth</el-radio>
    </el-radio-group>
    <div v-if="localAuthType === 'bearer'" class="auth-fields">
      <el-input v-model="localAuthConfig.token" placeholder="Enter token" @blur="emitUpdate" />
    </div>
    <div v-if="localAuthType === 'basic'" class="auth-fields">
      <el-input v-model="localAuthConfig.username" placeholder="Username" @blur="emitUpdate" />
      <el-input v-model="localAuthConfig.password" placeholder="Password" type="password" show-password @blur="emitUpdate" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: 'none' },
  authConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue', 'update:authConfig'])

const localAuthType = ref(props.modelValue)
const localAuthConfig = ref({ ...props.authConfig })

watch(() => props.modelValue, (v) => { localAuthType.value = v })
watch(() => props.authConfig, (v) => { localAuthConfig.value = { ...v } }, { deep: true })
watch(localAuthType, emitUpdate)

function emitUpdate() {
  emit('update:modelValue', localAuthType.value)
  emit('update:authConfig', { type: localAuthType.value, ...localAuthConfig.value })
}
</script>

<style scoped>
.auth-editor {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.auth-type-select {
  display: flex;
  gap: 12px;
}

.auth-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  max-width: 680px;
}

.auth-fields .el-input:first-child:last-child {
  grid-column: 1 / -1;
}
</style>
