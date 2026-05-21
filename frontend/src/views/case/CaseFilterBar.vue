<template>
  <div class="case-filter-bar">
    <el-form :inline="false" class="filter-form">
      <el-row :gutter="12">
        <el-col v-if="caseType === 'api'" :xs="24" :sm="12" :md="6" :lg="5">
          <el-form-item label="请求方式：" class="filter-item">
            <el-select
              :model-value="modelValue.methods"
              multiple
              clearable
              collapse-tags
              placeholder="请求方式"
              class="filter-control"
              @update:model-value="update('methods', $event)"
            >
              <el-option v-for="method in methodOptions" :key="method" :label="method" :value="method" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-form-item label="优先级：" class="filter-item">
            <el-select
              :model-value="modelValue.priorities"
              multiple
              clearable
              collapse-tags
              placeholder="优先级"
              class="filter-control"
              @update:model-value="update('priorities', $event)"
            >
              <el-option v-for="priority in priorityOptions" :key="priority" :label="priority" :value="priority" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-form-item label="自动化：" class="filter-item">
            <el-select
              :model-value="modelValue.isAutomated"
              clearable
              placeholder="自动化状态"
              class="filter-control"
              @update:model-value="update('isAutomated', $event)"
            >
              <el-option label="已自动化" :value="true" />
              <el-option label="未自动化" :value="false" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="7">
          <el-form-item label="创建日期：" class="filter-item">
            <el-date-picker
              class="filter-range"
              :model-value="modelValue.createdRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              unlink-panels
              @update:model-value="update('createdRange', $event || [])"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script setup>
import { methodOptions, priorityOptions } from './caseUtils'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  caseType: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue'])

function update(key, value) {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value,
  })
}
</script>

<style scoped>
.case-filter-bar {
  width: 100%;
}

.filter-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
}

.filter-form :deep(.el-row) {
  align-items: flex-end;
}

.filter-item {
  margin-bottom: 0;
  width: 100%;
}

.filter-control {
  width: 100%;
}

.filter-range {
  width: 100%;
}
</style>
