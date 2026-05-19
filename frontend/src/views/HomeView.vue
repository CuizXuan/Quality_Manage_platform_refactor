<template>
  <div class="home-view">
    <h1>Welcome to Quality Manage Platform</h1>
    <p data-testid="welcome-message">{{ message }}</p>
    <button @click="incrementCount" data-testid="increment-btn">Count: {{ count }}</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const message = ref('Welcome to the platform')
const count = ref(0)

function incrementCount() {
  count.value++
}
</script>

<style scoped>
.home-view {
  padding: 20px;
}
</style>
