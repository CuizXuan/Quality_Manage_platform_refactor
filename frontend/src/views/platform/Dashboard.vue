<template>
  <div class="dashboard-grid">
    <section class="hero-panel">
      <span class="section-kicker">Platform Foundation</span>
      <h2>新的质量管理平台底座已经就绪</h2>
      <p>当前阶段只保留登录页，其他模块按新体系重建。系统管理先提供用户、角色、组织、菜单四个基础域。</p>
    </section>

    <section v-for="item in cards" :key="item.title" class="metric-panel">
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
      <p>{{ item.title }}</p>
    </section>
  </div>
</template>

<script setup>
const cards = [
  { label: 'Identity', value: '4', title: '用户、角色、权限、登录态' },
  { label: 'Governance', value: '2', title: '组织与菜单治理' },
  { label: 'Theme', value: '2', title: '深色与浅色主题' },
]
</script>

