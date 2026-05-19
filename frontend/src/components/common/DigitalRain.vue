<template>
  <div class="ambient-gradient"></div>
</template>

<script setup>
</script>

<style scoped>
.ambient-gradient {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(91, 140, 255, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(124, 77, 255, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(91, 140, 255, 0.03) 0%, transparent 70%);
  animation: ambientPulse 20s ease-in-out infinite;
}

@keyframes ambientPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
