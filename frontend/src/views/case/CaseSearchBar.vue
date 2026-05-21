<template>
  <section class="case-search-bar">
    <el-form-item label="关键词：" class="search-item">
      <el-input
        :model-value="keyword"
        :prefix-icon="Search"
        clearable
        placeholder="搜索用例名称"
        @keyup.enter="emit('search')"
        @update:model-value="emit('update:keyword', $event)"
      />
    </el-form-item>

    <div class="case-search-bar__actions">
      <el-button type="primary" :icon="Search" @click="emit('search')">查询</el-button>
      <el-button :icon="RefreshLeft" @click="emit('reset')">重置</el-button>
      <el-button class="case-search-bar__primary" type="primary" :icon="Plus" @click="emit('create')">
        新增{{ caseTitle }}
      </el-button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, RefreshLeft, Search } from '@element-plus/icons-vue'

const props = defineProps({
  keyword: {
    type: String,
    default: '',
  },
  caseType: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update:keyword', 'search', 'reset', 'create'])

const caseTitle = computed(() => (props.caseType === 'api' ? '接口用例' : '功能用例'))
</script>

<style scoped>
.case-search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.search-item {
  margin-bottom: 0;
}

.search-item :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
}

.search-item :deep(.el-input) {
  width: 280px;
}

.case-search-bar :deep(.el-input__wrapper) {
  min-height: 34px;
}

.case-search-bar__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-left: auto;
}

.case-search-bar__actions :deep(.el-button) {
  min-width: 76px;
  height: 34px;
  margin-left: 0;
}

.case-search-bar__primary {
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.case-search-bar__primary:hover {
  transform: scale(1.02);
  filter: brightness(1.04);
}
</style>
