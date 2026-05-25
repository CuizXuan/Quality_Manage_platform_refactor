<template>
  <div class="case-filter-bar">
    <el-form :inline="false" class="filter-form">
      <el-row :gutter="12">
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-form-item label="项目：" class="filter-item">
            <el-select
              :model-value="modelValue.projectId"
              clearable
              placeholder="选择项目"
              class="filter-control"
              @update:model-value="onProjectChange($event)"
            >
              <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-form-item label="版本：" class="filter-item">
            <el-select
              :model-value="modelValue.versionId"
              clearable
              placeholder="选择版本"
              class="filter-control"
              :disabled="!modelValue.projectId"
              @update:model-value="onVersionChange($event)"
            >
              <el-option v-for="v in versionOptions" :key="v.id" :label="v.name" :value="v.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-form-item label="迭代：" class="filter-item">
            <el-select
              :model-value="modelValue.iterationId"
              clearable
              placeholder="选择迭代"
              class="filter-control"
              :disabled="!modelValue.versionId"
              @update:model-value="update('iterationId', $event)"
            >
              <el-option v-for="i in iterationOptions" :key="i.id" :label="i.name" :value="i.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="4">
          <el-form-item label="需求：" class="filter-item">
            <el-select
              :model-value="modelValue.requirementId"
              clearable
              placeholder="选择需求"
              class="filter-control"
              :disabled="!modelValue.projectId"
              @update:model-value="update('requirementId', $event)"
            >
              <el-option v-for="r in requirementOptions" :key="r.id" :label="r.title" :value="r.id" />
            </el-select>
          </el-form-item>
        </el-col>
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
import { computed, onMounted } from 'vue'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'
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

const store = useQualityFoundationStore()
const { projects, fetchProjects, versions, fetchVersions, iterations, fetchIterations, requirements, fetchRequirements } = store

const projectOptions = computed(() => store.projects)
const versionOptions = computed(() => store.versions)
const iterationOptions = computed(() => store.iterations)
const requirementOptions = computed(() => store.requirements)

onMounted(() => {
  fetchProjects({ page: 1, page_size: 100 })
})

function onProjectChange(projectId) {
  update('projectId', projectId)
  update('versionId', null)
  update('iterationId', null)
  update('requirementId', null)
  if (projectId) {
    fetchVersions({ project_id: projectId })
    fetchRequirements({ project_id: projectId, page: 1, page_size: 100 })
  }
}

function onVersionChange(versionId) {
  update('versionId', versionId)
  update('iterationId', null)
  update('requirementId', null)
  if (versionId) {
    const projectId = props.modelValue.projectId
    fetchIterations({ project_id: projectId, version_id: versionId })
  }
}

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
  row-gap: 8px;
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
