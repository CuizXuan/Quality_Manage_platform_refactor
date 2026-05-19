<template>
  <div class="case-redirect">
    <el-skeleton :rows="5" animated />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  router.replace('/case/api')
})
</script>

<style scoped>
.case-redirect {
  padding: 20px;
}
</style>
