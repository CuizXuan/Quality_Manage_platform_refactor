<template>
  <div class="case-center-page">
    <div class="case-center-page__ambient" aria-hidden="true">
      <div class="case-center-page__circuit circuit-a">
        <span>API</span>
        <i></i>
        <span>CASE</span>
        <i></i>
        <span>RUN</span>
        <i></i>
        <span>ASSERT</span>
      </div>
      <div class="case-center-page__circuit circuit-b">
        <span>REQ</span>
        <i></i>
        <span>DATA</span>
        <i></i>
        <span>CHECK</span>
      </div>
      <span class="case-center-page__data-line line-a"></span>
      <span class="case-center-page__data-line line-b"></span>
      <span class="case-center-page__data-line line-c"></span>
    </div>
    <header class="case-center-page__header">
      <div>
        <h1>用例管理</h1>
        <p>统计区、筛选区与资产列表分层呈现，实时度量自动化覆盖情况。</p>
      </div>
      <div class="case-center-page__header-flow" aria-hidden="true">
        <span>API</span>
        <i></i>
        <span>CASE</span>
        <i></i>
        <span>RUN</span>
      </div>
    </header>

    <CaseStatCards :stats="stats" :active-type="activeTab" />

    <el-tabs v-model="activeTab" class="case-center-page__tabs">
      <el-tab-pane label="接口用例" name="api">
        <CaseModulePage
          v-if="activeTab === 'api'"
          case-type="api"
          @stats-change="updateStats"
        />
      </el-tab-pane>
      <el-tab-pane label="功能用例" name="functional">
        <CaseModulePage
          v-if="activeTab === 'functional'"
          case-type="functional"
          @stats-change="updateStats"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseModulePage from './CaseModulePage.vue'
import CaseStatCards from './CaseStatCards.vue'

const activeTab = ref('api')
const stats = ref({
  total: 0,
  api_total: 0,
  functional_total: 0,
  current_total: 0,
  automated: 0,
  coverage: 0,
})

function updateStats(payload) {
  stats.value = {
    ...stats.value,
    ...payload,
  }
}
</script>

<style scoped>
.case-center-page {
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
}

.case-center-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.case-center-page::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: case-particles 18s ease-in-out infinite alternate;
}

.case-center-page__ambient {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.case-center-page__circuit {
  position: absolute;
  display: inline-grid;
  grid-auto-flow: column;
  gap: 12px;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: var(--border-radius-base);
  color: rgba(125, 211, 252, 0.68);
  background: rgba(15, 23, 42, 0.28);
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

html:not(.dark) .case-center-page__circuit {
  color: rgba(14, 116, 144, 0.52);
  background: rgba(255, 255, 255, 0.34);
}

.case-center-page__circuit span {
  display: inline-flex;
  align-items: center;
}

.case-center-page__circuit span::before {
  width: 6px;
  height: 6px;
  margin-right: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 12px currentColor;
  content: "";
}

.case-center-page__circuit i {
  position: relative;
  width: 54px;
  height: 1px;
  background: linear-gradient(90deg, currentColor, transparent);
  opacity: 0.86;
}

.case-center-page__circuit i::after {
  position: absolute;
  top: -2px;
  right: 0;
  width: 5px;
  height: 5px;
  border-top: 1px solid currentColor;
  border-right: 1px solid currentColor;
  content: "";
  transform: rotate(45deg);
}

.circuit-a {
  top: 88px;
  right: 6%;
  opacity: 0.72;
  animation: case-flow-a 16s ease-in-out infinite;
}

.circuit-b {
  bottom: 12%;
  left: 6%;
  opacity: 0.46;
  transform: scale(0.92);
  transform-origin: left center;
  animation: case-flow-b 20s ease-in-out infinite;
}

.case-center-page__data-line {
  position: absolute;
  height: 1px;
  border-radius: var(--border-radius-round);
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.92), transparent);
  opacity: 0.68;
}

.line-a {
  top: 18%;
  left: 18%;
  width: 34%;
  animation: case-line-a 8s ease-in-out infinite;
}

.line-b {
  right: 6%;
  top: 48%;
  width: 28%;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 166, 0.6), transparent);
  animation: case-line-b 11s ease-in-out infinite;
}

.line-c {
  bottom: 16%;
  left: 10%;
  width: 22%;
  opacity: 0.28;
  animation: case-line-c 13s ease-in-out infinite;
}

.case-center-page__header {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
}

.case-center-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .case-center-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.case-center-page__header h1,
.case-center-page__header p {
  margin: 0;
}

.case-center-page__header-flow {
  position: relative;
  z-index: 1;
  display: inline-grid;
  grid-auto-flow: column;
  gap: 10px;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: var(--border-radius-base);
  color: rgba(125, 211, 252, 0.78);
  background: rgba(8, 18, 32, 0.32);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.case-center-page__header-flow span {
  display: inline-flex;
  align-items: center;
}

.case-center-page__header-flow span::before {
  width: 6px;
  height: 6px;
  margin-right: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 12px currentColor;
  content: "";
}

.case-center-page__header-flow i {
  width: 48px;
  height: 1px;
  background: linear-gradient(90deg, currentColor, transparent);
}

html:not(.dark) .case-center-page__header-flow {
  color: rgba(14, 116, 144, 0.62);
  background: rgba(255, 255, 255, 0.32);
}

.case-center-page__header h1 {
  position: relative;
  z-index: 1;
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.case-center-page__header p {
  position: relative;
  z-index: 1;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.case-center-page__tabs {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  min-height: 0;
  min-width: 0;
  flex-direction: column;
}

.case-center-page__tabs :deep(.el-tabs__header) {
  margin: 0 0 10px;
  padding: 0 14px;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.58);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
}

html:not(.dark) .case-center-page__tabs :deep(.el-tabs__header) {
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

.case-center-page__tabs :deep(.el-tabs__item) {
  height: 40px;
  padding: 0 18px;
  font-weight: 800;
}

.case-center-page__tabs :deep(.el-tabs__item.is-active) {
  color: #38bdf8;
}

.case-center-page__tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.case-center-page__tabs :deep(.el-tabs__content),
.case-center-page__tabs :deep(.el-tab-pane) {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
}

@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-line-a {
  0%, 100% { transform: translate3d(-24px, 0, 0); opacity: 0.22; }
  50% { transform: translate3d(34px, 0, 0); opacity: 0.52; }
}

@keyframes case-line-b {
  0%, 100% { transform: translate3d(28px, 0, 0); opacity: 0.18; }
  50% { transform: translate3d(-42px, 0, 0); opacity: 0.48; }
}

@keyframes case-line-c {
  0%, 100% { transform: translate3d(0, 0, 0); opacity: 0.14; }
  50% { transform: translate3d(56px, 0, 0); opacity: 0.34; }
}

@keyframes case-flow-a {
  0%, 100% { transform: translate3d(0, 0, 0); opacity: 0.3; }
  50% { transform: translate3d(-24px, 8px, 0); opacity: 0.46; }
}

@keyframes case-flow-b {
  0%, 100% { transform: translate3d(0, 0, 0) scale(0.9); opacity: 0.2; }
  50% { transform: translate3d(28px, -8px, 0) scale(0.9); opacity: 0.32; }
}

@media (prefers-reduced-motion: reduce) {
  .case-center-page::before,
  .case-center-page::after,
  .case-center-page__data-line,
  .case-center-page__circuit {
    animation: none;
  }
}
</style>
