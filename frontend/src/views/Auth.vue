<template>
  <div class="auth-page">
    <canvas id="ai-network" class="network-canvas"></canvas>
    <div class="aurora-field" aria-hidden="true"></div>
    <div class="noise-layer"></div>
    <div class="grid-layer"></div>

    <header class="site-header">
      <button class="brand-lockup" type="button" @click="closeAuthPanel">
        <span class="brand-mark">
          <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <path d="M16 3L5 9l11 6 11-6-11-6Z" fill="url(#brandGrad)" />
            <path d="M5 16l11 6 11-6M5 22l11 6 11-6" stroke="url(#brandGrad)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            <defs>
              <linearGradient id="brandGrad" x1="4" y1="3" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                <stop stop-color="#7dd3fc" />
                <stop offset="0.54" stop-color="#6d5dfc" />
                <stop offset="1" stop-color="#2dd4bf" />
              </linearGradient>
            </defs>
          </svg>
        </span>
        <span class="brand-name">灵测 AI</span>
      </button>

      <div class="header-actions">
        <button class="login-entry" type="button" @click="openAuthPanel('login')">登录工作台</button>
      </div>
    </header>

    <nav class="section-locator" aria-label="页面定位导航">
      <a href="#capabilities">
        <span>01</span>
        能力矩阵
      </a>
      <a href="#console">
        <span>02</span>
        质量中台
      </a>
      <a href="#scenarios">
        <span>03</span>
        场景数据
      </a>
      <a href="#insights">
        <span>04</span>
        智能闭环
      </a>
    </nav>

    <main class="landing-shell">
      <section class="hero-section" aria-labelledby="hero-title">
        <div class="hero-copy">
          <span class="eyebrow">
            <span class="live-dot"></span>
            AI Quality Command Center
          </span>
          <div class="hero-title-wrap">
            <span
              v-for="particle in titleParticles"
              :key="particle.id"
              class="title-particle"
              :style="particle.style"
              aria-hidden="true"
            ></span>
            <h1 id="hero-title">把质量信号转化为发布确定性</h1>
          </div>
          <p>
            把需求、接口、自动化、缺陷和发布风险串成一条可观测的质量流，让团队在发布前看清每个信号、每次变化和每个决策依据。
          </p>
          <div class="hero-actions">
            <button class="primary-action" type="button" @click="openAuthPanel('login')">
              进入工作台
              <span aria-hidden="true">→</span>
            </button>
            <button class="secondary-action" type="button" @click="scrollToConsole">浏览能力矩阵</button>
          </div>

          <div class="hero-proof" aria-label="平台关键指标">
            <div v-for="item in heroMetrics" :key="item.label" class="hero-proof-item">
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </div>

        <div class="hero-visual">
          <div id="console" class="console-stage" aria-label="AI 质量工程能力大屏">
            <div class="console-topbar">
              <div>
                <span class="console-kicker">Quality Command Center</span>
                <strong>Release Intelligence</strong>
              </div>
              <div class="console-tabs" aria-hidden="true">
                <span>Plan</span>
                <span>Run</span>
                <span>Gate</span>
              </div>
              <div class="console-status">
                <span></span>
                Live Sync
              </div>
            </div>

            <div class="console-flow" aria-label="质量信号流">
              <span>Demand</span>
              <i></i>
              <span>API</span>
              <i></i>
              <span>Case</span>
              <i></i>
              <span>Risk</span>
              <i></i>
              <span>Release</span>
            </div>

            <div class="console-intel-row" aria-label="AI 决策提示">
              <article v-for="item in consoleSignals" :key="item.label" class="console-intel-card">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
                <p>{{ item.copy }}</p>
              </article>
            </div>

            <div class="console-metrics">
              <div class="metric-card major">
                <span>发布风险</span>
                <strong>Low</strong>
                <div class="risk-line">
                  <span style="height: 34%"></span>
                  <span style="height: 52%"></span>
                  <span style="height: 45%"></span>
                  <span style="height: 28%"></span>
                  <span style="height: 22%"></span>
                </div>
              </div>
              <div class="metric-card">
                <span>覆盖率</span>
                <strong>92%</strong>
                <em>+8.4%</em>
              </div>
              <div class="metric-card">
                <span>自动化率</span>
                <strong>78%</strong>
                <em>rolling</em>
              </div>
              <div class="metric-card">
                <span>失败聚类</span>
                <strong>12</strong>
                <em>3 high</em>
              </div>
            </div>

            <div id="capabilities" class="capability-grid">
              <article
                v-for="(item, index) in capabilityCards"
                :key="item.title"
                class="capability-card"
                :style="{ '--i': index }"
              >
                <span class="card-icon">{{ item.icon }}</span>
                <div class="card-body">
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.copy }}</p>
                </div>
                <span class="card-state">{{ item.state }}</span>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section id="scenarios" class="insight-strip" aria-label="质量场景数据">
        <div v-for="item in insightStats" :key="item.label" class="insight-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.trend }}</em>
        </div>
      </section>

      <section class="flow-ribbon" aria-label="质量信号流动">
        <div class="marquee-track">
          <template v-for="round in streamRounds" :key="`a-${round}`">
            <span v-for="item in streamItems" :key="`${round}-${item}`">{{ item }}</span>
          </template>
          <template v-for="round in streamRounds" :key="`b-${round}`">
            <span v-for="item in streamItems" :key="`copy-${round}-${item}`">{{ item }}</span>
          </template>
        </div>
      </section>

      <section id="insights" class="workflow-band" aria-label="智能质量流程">
        <div class="workflow-head">
          <span>AI TestOps Flow</span>
          <strong>从需求到发布，让每一步都可追踪、可解释、可决策。</strong>
        </div>
        <div class="workflow-steps">
          <article v-for="(step, index) in workflowSteps" :key="step.title">
            <em>{{ String(index + 1).padStart(2, '0') }}</em>
            <strong>{{ step.title }}</strong>
            <p>{{ step.copy }}</p>
          </article>
        </div>
      </section>
    </main>

    <Transition name="auth-panel">
      <div v-if="authPanelOpen" class="auth-overlay" @click.self="closeAuthPanel">
        <aside class="auth-panel" aria-label="账号登录">
          <button class="close-button" type="button" aria-label="关闭登录面板" @click="closeAuthPanel">×</button>

          <div class="panel-brand">
            <span class="panel-mark">
              <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
                <path d="M16 3L5 9l11 6 11-6-11-6Z" fill="url(#panelGrad)" />
                <path d="M5 16l11 6 11-6M5 22l11 6 11-6" stroke="url(#panelGrad)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                <defs>
                  <linearGradient id="panelGrad" x1="4" y1="3" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#7dd3fc" />
                    <stop offset="0.54" stop-color="#6d5dfc" />
                    <stop offset="1" stop-color="#2dd4bf" />
                  </linearGradient>
                </defs>
              </svg>
            </span>
            <div>
              <span>Protected Workspace</span>
              <strong>灵测 AI</strong>
            </div>
          </div>

          <div v-if="mode === 'login'" class="form-section">
            <div class="form-heading">
              <h2>登录工作台</h2>
              <p>继续进入企业级质量工程中台。</p>
            </div>

            <form class="auth-form" @submit.prevent="handleLogin">
              <label class="field">
                <span>用户名或邮箱</span>
                <input v-model="loginForm.username" type="text" placeholder="admin" :disabled="loading" />
              </label>

              <label class="field">
                <span>密码</span>
                <div class="password-field">
                  <input
                    v-model="loginForm.password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="输入密码"
                    :disabled="loading"
                  />
                  <button type="button" @click="showPassword = !showPassword">
                    {{ showPassword ? '隐藏' : '显示' }}
                  </button>
                </div>
              </label>

              <div v-if="error" class="error-message">{{ error }}</div>

              <div class="form-options">
                <label class="remember-me">
                  <input v-model="loginForm.remember" type="checkbox" />
                  <span></span>
                  记住登录状态
                </label>
                <em>Session protected</em>
              </div>

              <button class="submit-button" type="submit" :disabled="loading">
                {{ loading ? '登录中...' : '登录' }}
              </button>
            </form>

            <div class="form-footer">
              <span>还没有账号？</span>
              <button type="button" @click="switchMode('register')">创建账号</button>
            </div>
          </div>

          <div v-else class="form-section">
            <div class="form-heading">
              <h2>创建账号</h2>
              <p>接入团队质量工作台。</p>
            </div>

            <form class="auth-form" @submit.prevent="handleRegister">
              <label class="field">
                <span>用户名</span>
                <input v-model="registerForm.username" type="text" placeholder="设置用户名" :disabled="loading" />
              </label>

              <label class="field">
                <span>邮箱</span>
                <input v-model="registerForm.email" type="text" placeholder="team@example.com" :disabled="loading" />
              </label>

              <label class="field">
                <span>密码</span>
                <input v-model="registerForm.password" type="password" placeholder="至少 6 位" :disabled="loading" />
              </label>

              <div v-if="error" class="error-message">{{ error }}</div>

              <button class="submit-button" type="submit" :disabled="loading">
                {{ loading ? '创建中...' : '创建并进入' }}
              </button>
            </form>

            <div class="form-footer">
              <span>已有账号？</span>
              <button type="button" @click="switchMode('login')">返回登录</button>
            </div>
          </div>

          <div class="demo-account">
            <span>Demo account</span>
            <code>admin / admin123</code>
          </div>
        </aside>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref('login')
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const authPanelOpen = ref(false)

const loginForm = ref({
  username: '',
  password: '',
  remember: false
})

const registerForm = ref({
  username: '',
  email: '',
  password: ''
})

const heroMetrics = [
  { label: '发布前质量信号', value: '18.6k' },
  { label: '风险识别准确率', value: '91%' },
  { label: '平均反馈延迟', value: '24ms' }
]

const titleParticles = Array.from({ length: 24 }, (_, index) => ({
  id: index,
  style: {
    '--x': `${Math.random() * 100}%`,
    '--y': `${Math.random() * 100}%`,
    '--size': `${Math.random() * 5 + 3}px`,
    '--delay': `${Math.random() * 2.8}s`,
    '--duration': `${Math.random() * 3.4 + 3.8}s`
  }
}))

const consoleSignals = [
  { label: 'AI Suggestion', value: '阻断 3 个高风险发布项', copy: '基于失败簇、覆盖缺口和变更热区给出门禁建议。' },
  { label: 'Signal Stream', value: '需求、接口、日志实时汇聚', copy: '将多源质量信号收束到同一条发布决策链路。' }
]

const capabilityCards = [
  { icon: '01', title: 'AI 用例生成', copy: '从需求、接口和变更描述生成高覆盖测试集，并标记风险路径。', state: 'Ready' },
  { icon: '02', title: '接口智能解析', copy: '识别 cURL、OpenAPI 与请求链路，自动沉淀可复用资产。', state: 'Parse' },
  { icon: '03', title: '自动化回归', copy: '按发布窗口调度测试集，输出变更影响范围与执行建议。', state: 'Run' },
  { icon: '04', title: '风险预测', copy: '结合模块、提交、缺陷历史和覆盖变化计算发布风险。', state: 'Score' },
  { icon: '05', title: '缺陷聚类', copy: '把失败日志、异常堆栈和接口错误归因聚合成问题簇。', state: 'Cluster' },
  { icon: '06', title: '质量门禁', copy: '发布前自动评估准入条件、阻断项和豁免理由。', state: 'Gate' }
]

const insightStats = [
  { label: '自动化场景', value: '2,480+', trend: '持续回归中' },
  { label: '接口资产', value: '18.6k', trend: '跨项目复用' },
  { label: '风险识别', value: '91%', trend: '发布前预判' },
  { label: '平均反馈', value: '24ms', trend: '实时信号同步' }
]

const streamItems = ['需求解析', '接口资产', '用例生成', '自动回归', '缺陷聚类', '风险评分', '质量门禁', '发布洞察']
const streamRounds = Array.from({ length: 6 }, (_, index) => index + 1)

const workflowSteps = [
  { title: '需求解析', copy: '把需求、变更和接口信息拆成可测试信号。' },
  { title: '用例生成', copy: '自动补齐路径、边界、异常和回归集合。' },
  { title: '执行编排', copy: '按环境、优先级和发布窗口动态调度。' },
  { title: '风险决策', copy: '汇总覆盖、失败、缺陷和趋势形成门禁建议。' }
]

let canvas
let ctx
let particles
let animationId

function openAuthPanel(nextMode = 'login') {
  mode.value = nextMode
  error.value = ''
  authPanelOpen.value = true
}

function closeAuthPanel() {
  authPanelOpen.value = false
  error.value = ''
}

function switchMode(nextMode) {
  mode.value = nextMode
  error.value = ''
}

function scrollToConsole() {
  document.getElementById('console')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function handleLogin() {
  error.value = ''

  if (!loginForm.value.username.trim()) {
    error.value = '请输入用户名或邮箱'
    return
  }

  if (!loginForm.value.password) {
    error.value = '请输入密码'
    return
  }

  loading.value = true

  try {
    const success = await authStore.login(
      loginForm.value.username,
      loginForm.value.password,
      loginForm.value.remember
    )

    if (success) {
      router.push('/')
    } else {
      error.value = authStore.error || '登录失败'
    }
  } catch (err) {
    error.value = err.message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  error.value = ''

  if (!registerForm.value.username.trim()) {
    error.value = '请输入用户名'
    return
  }

  if (!registerForm.value.email.trim()) {
    error.value = '请输入邮箱'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(registerForm.value.email)) {
    error.value = '请输入有效的邮箱地址'
    return
  }

  if (registerForm.value.password.length < 6) {
    error.value = '密码长度至少 6 位'
    return
  }

  loading.value = true

  try {
    const success = await authStore.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password
    )

    if (success) {
      router.push('/')
    } else {
      error.value = authStore.error || '注册失败'
    }
  } catch (err) {
    error.value = err.message || '注册失败'
  } finally {
    loading.value = false
  }
}

function initNetwork() {
  canvas = document.getElementById('ai-network')
  if (!canvas) return

  ctx = canvas.getContext('2d')
  resizeCanvas()
  particles = Array.from({ length: 76 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.18,
    vy: (Math.random() - 0.5) * 0.18,
    radius: Math.random() * 1.5 + 0.4,
    alpha: Math.random() * 0.55 + 0.16
  }))
  animateNetwork()
}

function resizeCanvas() {
  if (!canvas) return
  canvas.width = window.innerWidth * window.devicePixelRatio
  canvas.height = window.innerHeight * window.devicePixelRatio
  canvas.style.width = '100vw'
  canvas.style.height = '100vh'
  ctx?.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0)
}

function animateNetwork() {
  if (!ctx || !canvas) return

  const width = window.innerWidth
  const height = window.innerHeight
  ctx.clearRect(0, 0, width, height)

  particles.forEach((particle, index) => {
    for (let i = index + 1; i < particles.length; i += 1) {
      const other = particles[i]
      const distance = Math.hypot(particle.x - other.x, particle.y - other.y)
      if (distance < 150) {
        ctx.strokeStyle = `rgba(125, 211, 252, ${0.11 * (1 - distance / 150)})`
        ctx.lineWidth = 0.7
        ctx.beginPath()
        ctx.moveTo(particle.x, particle.y)
        ctx.lineTo(other.x, other.y)
        ctx.stroke()
      }
    }

    ctx.fillStyle = `rgba(226, 232, 240, ${particle.alpha})`
    ctx.beginPath()
    ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2)
    ctx.fill()

    particle.x += particle.vx
    particle.y += particle.vy

    if (particle.x < 0 || particle.x > width) particle.vx *= -1
    if (particle.y < 0 || particle.y > height) particle.vy *= -1
  })

  animationId = requestAnimationFrame(animateNetwork)
}

onMounted(() => {
  initNetwork()
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  box-sizing: border-box;
}

.auth-page {
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  position: fixed;
  inset: 0;
  z-index: 10;
  overflow-x: hidden;
  overflow-y: auto;
  background:
    radial-gradient(circle at 28% 22%, rgba(45, 212, 191, 0.12), transparent 28%),
    radial-gradient(circle at 78% 18%, rgba(109, 93, 252, 0.16), transparent 32%),
    linear-gradient(135deg, #07090f 0%, #0b1118 42%, #090815 100%);
  color: #f8fafc;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  text-align: left;
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.network-canvas,
.noise-layer,
.grid-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.network-canvas {
  z-index: 0;
  opacity: 0.72;
}

.noise-layer {
  z-index: 1;
  opacity: 0.045;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.grid-layer {
  z-index: 2;
  background:
    linear-gradient(rgba(148, 163, 184, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.045) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.86), rgba(0, 0, 0, 0.18));
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  width: min(100% - 64px, 1440px);
  margin: 0 auto;
  padding: 24px 0 12px;
}

.site-header::before {
  content: '';
  position: absolute;
  inset: 10px -18px 0;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  background: rgba(7, 10, 18, 0.48);
  backdrop-filter: blur(18px);
  z-index: -1;
}

.brand-lockup,
.header-actions,
.main-nav {
  display: flex;
  align-items: center;
}

.brand-lockup {
  gap: 12px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.brand-mark,
.panel-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.14);
}

.brand-mark svg,
.panel-mark svg {
  width: 24px;
  height: 24px;
}

.brand-name {
  font-size: 16px;
  font-weight: 800;
}

.main-nav {
  gap: 28px;
}

.main-nav a {
  color: rgba(226, 232, 240, 0.68);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s ease;
}

.main-nav a:hover {
  color: #ffffff;
}

.header-actions {
  gap: 12px;
}

.ghost-action,
.login-entry,
.primary-action,
.secondary-action {
  border: 0;
  font: inherit;
  cursor: pointer;
}

.ghost-action {
  padding: 10px 14px;
  border-radius: 8px;
  background: transparent;
  color: rgba(226, 232, 240, 0.7);
  font-weight: 700;
}

.login-entry {
  padding: 10px 18px;
  border-radius: 8px;
  background: #f8fafc;
  color: #050816;
  font-weight: 800;
}

.landing-shell {
  position: relative;
  z-index: 5;
  width: min(100% - 64px, 1440px);
  margin: 0 auto;
}

.hero-section {
  display: grid;
  grid-template-columns: minmax(360px, 0.82fr) minmax(640px, 1.18fr);
  gap: 54px;
  align-items: center;
  min-height: calc(100vh - 84px);
  padding: 54px 0 42px;
}

.hero-copy {
  max-width: 620px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 22px;
  padding: 9px 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.42);
  color: rgba(226, 232, 240, 0.7);
  font-size: 12px;
  font-weight: 700;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2dd4bf;
  box-shadow: 0 0 12px rgba(45, 212, 191, 0.8);
}

.hero-copy h1 {
  margin: 0;
  color: #f8fafc;
  font-size: clamp(44px, 5.5vw, 84px);
  line-height: 1.02;
  letter-spacing: 0;
  font-weight: 800;
}

.hero-copy p {
  width: min(100%, 560px);
  margin: 24px 0 0;
  color: rgba(226, 232, 240, 0.68);
  font-size: 18px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 34px;
}

.primary-action,
.secondary-action {
  min-height: 46px;
  padding: 0 20px;
  border-radius: 8px;
  font-weight: 800;
}

.primary-action {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #f8fafc, #c7d2fe);
  color: #050816;
  box-shadow: 0 18px 48px rgba(109, 93, 252, 0.24);
}

.secondary-action {
  border: 1px solid rgba(226, 232, 240, 0.18);
  background: rgba(15, 23, 42, 0.46);
  color: #f8fafc;
}

.console-stage {
  position: relative;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.82), rgba(6, 11, 20, 0.74)),
    rgba(15, 23, 42, 0.44);
  box-shadow:
    0 36px 90px rgba(0, 0, 0, 0.38),
    inset 0 1px rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(22px);
  overflow: hidden;
}

.console-stage::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(125, 211, 252, 0.08), transparent 28%, rgba(45, 212, 191, 0.08)),
    linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: auto, 100% 38px;
  pointer-events: none;
}

.console-topbar,
.console-metrics,
.capability-grid {
  position: relative;
  z-index: 1;
}

.console-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 10px 10px 18px;
}

.console-kicker {
  display: block;
  margin-bottom: 6px;
  color: rgba(148, 163, 184, 0.72);
  font-size: 12px;
  font-weight: 700;
}

.console-topbar strong {
  font-size: 20px;
}

.console-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(226, 232, 240, 0.76);
  font-size: 13px;
  font-weight: 800;
}

.console-status span {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #2dd4bf;
  box-shadow: 0 0 14px rgba(45, 212, 191, 0.74);
}

.console-metrics {
  display: grid;
  grid-template-columns: 1.35fr repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.metric-card,
.capability-card,
.insight-item,
.workflow-band {
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(15, 23, 42, 0.56);
}

.metric-card {
  min-height: 104px;
  padding: 16px;
}

.metric-card span {
  display: block;
  color: rgba(203, 213, 225, 0.62);
  font-size: 13px;
  font-weight: 700;
}

.metric-card strong {
  display: block;
  margin-top: 12px;
  font-size: 30px;
}

.metric-card.major strong {
  color: #34d399;
}

.risk-line {
  display: flex;
  align-items: flex-end;
  gap: 7px;
  height: 36px;
  margin-top: 12px;
}

.risk-line span {
  flex: 1;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, #2dd4bf, rgba(45, 212, 191, 0.16));
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.capability-card {
  min-height: 156px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
  padding: 16px;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.capability-card:hover {
  transform: translateY(-3px);
  border-color: rgba(125, 211, 252, 0.34);
  background: rgba(15, 23, 42, 0.72);
}

.card-icon,
.card-state {
  color: rgba(125, 211, 252, 0.82);
  font-size: 12px;
  font-weight: 800;
}

.capability-card h3 {
  margin: 0 0 8px;
  color: #f8fafc;
  font-size: 16px;
}

.capability-card p {
  margin: 0;
  color: rgba(203, 213, 225, 0.62);
  font-size: 13px;
  line-height: 1.6;
}

.insight-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 0 0 48px;
}

.insight-item {
  padding: 18px;
}

.insight-item span {
  display: block;
  color: rgba(203, 213, 225, 0.62);
  font-size: 13px;
  font-weight: 700;
}

.insight-item strong {
  display: block;
  margin-top: 8px;
  color: #f8fafc;
  font-size: 26px;
}

.workflow-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 60px;
  padding: 22px;
}

.workflow-head span {
  display: block;
  margin-bottom: 6px;
  color: rgba(125, 211, 252, 0.72);
  font-size: 12px;
  font-weight: 800;
}

.workflow-head strong {
  font-size: 20px;
}

.workflow-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.workflow-steps div {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.055);
  color: rgba(226, 232, 240, 0.74);
  font-size: 13px;
  font-weight: 700;
}

.auth-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  justify-content: flex-end;
  background: rgba(3, 7, 18, 0.56);
  backdrop-filter: blur(12px);
}

.auth-panel {
  position: relative;
  width: min(100%, 440px);
  min-height: 100vh;
  padding: 34px;
  border-left: 1px solid rgba(148, 163, 184, 0.16);
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(8, 13, 24, 0.96)),
    #0b1118;
  box-shadow: -32px 0 80px rgba(0, 0, 0, 0.34);
}

.auth-panel-enter-active,
.auth-panel-leave-active {
  transition: opacity 0.25s ease;
}

.auth-panel-enter-active .auth-panel,
.auth-panel-leave-active .auth-panel {
  transition: transform 0.25s ease;
}

.auth-panel-enter-from,
.auth-panel-leave-to {
  opacity: 0;
}

.auth-panel-enter-from .auth-panel,
.auth-panel-leave-to .auth-panel {
  transform: translateX(32px);
}

.close-button {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 34px;
  height: 34px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(226, 232, 240, 0.72);
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}

.panel-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 42px;
}

.panel-brand span {
  color: rgba(203, 213, 225, 0.6);
  font-size: 12px;
  font-weight: 800;
}

.panel-brand strong {
  display: block;
  margin-top: 4px;
  color: #f8fafc;
  font-size: 22px;
}

.form-heading h2 {
  margin: 0;
  font-size: 30px;
}

.form-heading p {
  margin: 10px 0 0;
  color: rgba(203, 213, 225, 0.64);
  line-height: 1.7;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 28px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 9px;
  color: rgba(226, 232, 240, 0.72);
  font-size: 13px;
  font-weight: 800;
}

.field input,
.password-field {
  width: 100%;
  min-height: 48px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.055);
  color: #f8fafc;
}

.field input {
  padding: 0 14px;
  outline: none;
}

.field input::placeholder {
  color: rgba(148, 163, 184, 0.52);
}

.field input:focus,
.password-field:focus-within {
  border-color: rgba(125, 211, 252, 0.52);
  box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.1);
}

.password-field {
  display: flex;
  align-items: center;
}

.password-field input {
  min-height: 46px;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.password-field button {
  flex: 0 0 auto;
  margin-right: 8px;
  border: 0;
  background: transparent;
  color: rgba(125, 211, 252, 0.82);
  cursor: pointer;
  font-weight: 800;
}

.error-message {
  padding: 12px;
  border: 1px solid rgba(248, 113, 113, 0.24);
  border-radius: 8px;
  background: rgba(248, 113, 113, 0.1);
  color: #fecaca;
  font-size: 13px;
  line-height: 1.5;
}

.form-options {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  color: rgba(203, 213, 225, 0.64);
  font-size: 13px;
}

.remember-me {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
}

.remember-me input {
  display: none;
}

.remember-me span {
  position: relative;
  width: 17px;
  height: 17px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.05);
}

.remember-me input:checked + span {
  background: #7dd3fc;
  border-color: #7dd3fc;
}

.remember-me input:checked + span::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 4px;
  height: 8px;
  border-right: 2px solid #04111f;
  border-bottom: 2px solid #04111f;
  transform: rotate(45deg);
}

.form-options em {
  color: rgba(125, 211, 252, 0.72);
  font-style: normal;
  font-weight: 800;
}

.submit-button {
  min-height: 50px;
  border: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #7dd3fc, #6d5dfc);
  color: #f8fafc;
  cursor: pointer;
  font-size: 15px;
  font-weight: 800;
  box-shadow: 0 18px 34px rgba(109, 93, 252, 0.28);
}

.submit-button:disabled {
  opacity: 0.68;
  cursor: not-allowed;
}

.form-footer {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  color: rgba(203, 213, 225, 0.58);
  font-size: 13px;
}

.form-footer button {
  border: 0;
  background: transparent;
  color: rgba(125, 211, 252, 0.86);
  cursor: pointer;
  font: inherit;
  font-weight: 800;
}

.demo-account {
  margin-top: 28px;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.045);
}

.demo-account span {
  display: block;
  margin-bottom: 8px;
  color: rgba(203, 213, 225, 0.58);
  font-size: 12px;
  font-weight: 800;
}

.demo-account code {
  color: #f8fafc;
  font-family: Consolas, 'SFMono-Regular', monospace;
}

@media (max-width: 1180px) {
  .hero-section {
    grid-template-columns: 1fr;
    padding-top: 42px;
  }

  .hero-copy {
    max-width: 780px;
  }

  .main-nav {
    display: none;
  }
}

@media (max-width: 820px) {
  .site-header,
  .landing-shell {
    width: min(100% - 32px, 1440px);
  }

  .site-header {
    gap: 14px;
  }

  .ghost-action {
    display: none;
  }

  .hero-section {
    min-height: auto;
    padding: 34px 0 28px;
  }

  .hero-copy h1 {
    font-size: 42px;
  }

  .hero-copy p {
    font-size: 16px;
  }

  .console-metrics,
  .capability-grid,
  .insight-strip {
    grid-template-columns: 1fr;
  }

  .workflow-band {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 520px) {
  .brand-name {
    display: none;
  }

  .hero-actions {
    flex-direction: column;
  }

  .primary-action,
  .secondary-action {
    width: 100%;
  }

  .auth-panel {
    padding: 28px 20px;
  }

  .form-options {
    flex-direction: column;
  }
}

/* Landing redesign overrides */
.auth-page {
  --page-gutter: clamp(20px, 4vw, 72px);
  --cyan: #47f0dc;
  --sky: #8fd8ff;
  --ink: #071018;
  --panel: rgba(8, 18, 32, 0.74);
  --panel-strong: rgba(11, 24, 43, 0.88);
  position: fixed;
  min-height: 100svh;
  background:
    radial-gradient(circle at 14% 18%, rgba(71, 240, 220, 0.18), transparent 27%),
    radial-gradient(circle at 88% 12%, rgba(143, 216, 255, 0.16), transparent 29%),
    radial-gradient(circle at 80% 80%, rgba(109, 93, 252, 0.13), transparent 33%),
    linear-gradient(120deg, #05080f 0%, #071018 44%, #070b18 100%);
  scroll-behavior: smooth;
}

.auth-page::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0%, rgba(71, 240, 220, 0.06) 34%, transparent 58%),
    linear-gradient(290deg, transparent 18%, rgba(143, 216, 255, 0.045) 46%, transparent 72%);
  animation: auroraDrift 14s ease-in-out infinite alternate;
}

.aurora-field {
  position: absolute;
  inset: -18% -10% auto;
  z-index: 0;
  height: 62vh;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 24% 42%, rgba(71, 240, 220, 0.28), transparent 34%),
    radial-gradient(ellipse at 74% 32%, rgba(109, 93, 252, 0.22), transparent 37%);
  filter: blur(28px);
  opacity: 0.78;
  animation: glowPulse 8s ease-in-out infinite alternate;
}

.network-canvas,
.noise-layer,
.grid-layer {
  position: fixed;
}

.network-canvas {
  opacity: 0.58;
}

.grid-layer {
  background:
    linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(circle at 52% 22%, rgba(0, 0, 0, 0.9), transparent 78%);
}

.site-header {
  position: sticky;
  top: 0;
  width: 100%;
  max-width: none;
  min-height: 76px;
  margin: 0;
  padding: 14px var(--page-gutter);
  border-bottom: 1px solid rgba(226, 232, 240, 0.1);
  background: linear-gradient(180deg, rgba(4, 9, 17, 0.86), rgba(4, 9, 17, 0.56));
  backdrop-filter: blur(24px);
  box-shadow: 0 18px 52px rgba(0, 0, 0, 0.18);
}

.site-header::before {
  inset: auto;
  content: none;
}

.brand-lockup {
  gap: 14px;
  transition: transform 0.22s ease, opacity 0.22s ease;
}

.brand-lockup:hover {
  transform: translateY(-1px);
}

.brand-mark,
.panel-mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.035)),
    rgba(15, 23, 42, 0.72);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.18), 0 14px 34px rgba(71, 240, 220, 0.12);
}

.brand-name {
  font-size: 17px;
  letter-spacing: 0.08em;
}

.main-nav {
  gap: 6px;
  padding: 6px;
  border: 1px solid rgba(226, 232, 240, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.035);
}

.main-nav a {
  position: relative;
  padding: 9px 15px;
  border-radius: 999px;
  color: rgba(226, 232, 240, 0.7);
  font-size: 13px;
  transition: color 0.22s ease, background 0.22s ease, transform 0.22s ease;
}

.main-nav a:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.header-actions {
  gap: 10px;
  margin-left: auto;
}

.section-locator {
  position: fixed;
  right: clamp(18px, 2.4vw, 46px);
  top: 50%;
  z-index: 35;
  display: grid;
  gap: 12px;
  transform: translateY(-50%);
}

.section-locator a {
  position: relative;
  display: grid;
  grid-template-columns: 28px 1fr;
  align-items: center;
  gap: 10px;
  width: 126px;
  min-height: 44px;
  padding: 8px 12px 8px 8px;
  border: 1px solid rgba(226, 232, 240, 0.12);
  border-radius: 999px;
  background: rgba(6, 13, 24, 0.58);
  color: rgba(226, 232, 240, 0.78);
  font-size: 13px;
  font-weight: 800;
  line-height: 1;
  text-decoration: none;
  box-shadow: 0 14px 38px rgba(0, 0, 0, 0.22), inset 0 1px rgba(255, 255, 255, 0.055);
  backdrop-filter: blur(14px);
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease, color 0.22s ease;
}

.section-locator a::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 50%;
  width: 10px;
  height: 2px;
  border-radius: 999px;
  background: rgba(71, 240, 220, 0.28);
  transform: translateY(-50%);
  transition: width 0.22s ease, background 0.22s ease;
}

.section-locator span {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(71, 240, 220, 0.1);
  color: rgba(143, 216, 255, 0.9);
  font-size: 11px;
  font-weight: 900;
}

.section-locator a:hover,
.section-locator a:focus-visible {
  transform: translateX(-7px);
  border-color: rgba(143, 216, 255, 0.42);
  background: rgba(16, 34, 55, 0.84);
  color: #ffffff;
}

.section-locator a:hover::before,
.section-locator a:focus-visible::before {
  width: 18px;
  background: rgba(71, 240, 220, 0.82);
}

.ghost-action,
.login-entry,
.primary-action,
.secondary-action,
.submit-button,
.close-button {
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    border-color 0.22s ease,
    background 0.22s ease,
    color 0.22s ease;
}

.ghost-action {
  padding: 11px 16px;
  border: 1px solid rgba(226, 232, 240, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.045);
  color: rgba(226, 232, 240, 0.82);
}

.login-entry {
  padding: 12px 20px;
  border-radius: 999px;
  background: linear-gradient(135deg, #ffffff 0%, #d9f7ff 52%, #b8fff2 100%);
  color: #061018;
  box-shadow: 0 16px 38px rgba(71, 240, 220, 0.22);
}

.ghost-action:hover,
.login-entry:hover,
.primary-action:hover,
.secondary-action:hover,
.submit-button:hover,
.close-button:hover {
  transform: translateY(-2px);
}

.landing-shell {
  width: min(100% - calc(var(--page-gutter) * 2), 1680px);
  max-width: 1680px;
  padding-bottom: 84px;
}

#console,
#capabilities,
#scenarios,
#insights {
  scroll-margin-top: 104px;
}

.hero-section {
  grid-template-columns: minmax(440px, 0.9fr) minmax(680px, 1.1fr);
  gap: clamp(64px, 7vw, 128px);
  min-height: calc(100svh - 76px);
  padding: clamp(88px, 9vh, 132px) 0 clamp(70px, 8vh, 110px);
}

.hero-copy {
  position: relative;
  max-width: 720px;
  animation: riseIn 0.72s ease both;
}

.eyebrow {
  margin-bottom: 28px;
  padding: 10px 14px;
  border-radius: 999px;
  border-color: rgba(143, 216, 255, 0.22);
  background: rgba(8, 18, 32, 0.58);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.08);
}

.live-dot {
  animation: livePulse 1.8s ease-in-out infinite;
}

.hero-title-wrap {
  position: relative;
  isolation: isolate;
  width: fit-content;
  max-width: 780px;
}

.hero-title-wrap::before {
  content: '';
  position: absolute;
  inset: -18% -10% -8%;
  z-index: -2;
  pointer-events: none;
  background:
    radial-gradient(circle at 24% 28%, rgba(71, 240, 220, 0.22), transparent 26%),
    radial-gradient(circle at 72% 62%, rgba(143, 216, 255, 0.16), transparent 32%);
  filter: blur(26px);
  opacity: 0.82;
  animation: titleHalo 5.8s ease-in-out infinite alternate;
}

.hero-title-wrap::after {
  content: '';
  position: absolute;
  inset: 8% -4% 0;
  z-index: -1;
  pointer-events: none;
  background:
    linear-gradient(90deg, transparent 0%, rgba(71, 240, 220, 0.42) 50%, transparent 100%),
    linear-gradient(180deg, transparent 0%, rgba(143, 216, 255, 0.18) 58%, transparent 100%);
  mask-image: repeating-linear-gradient(90deg, #000 0 2px, transparent 2px 13px);
  opacity: 0.28;
  animation: scanLines 4.8s linear infinite;
}

.hero-copy h1 {
  position: relative;
  z-index: 2;
  max-width: 760px;
  font-size: clamp(56px, 6vw, 112px);
  line-height: 0.96;
  letter-spacing: -0.065em;
  text-wrap: balance;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.04);
}

.title-particle {
  position: absolute;
  left: var(--x);
  top: var(--y);
  z-index: 1;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  pointer-events: none;
  background: radial-gradient(circle, rgba(226, 255, 252, 0.98) 0%, rgba(71, 240, 220, 0.54) 42%, transparent 72%);
  box-shadow:
    0 0 12px rgba(71, 240, 220, 0.72),
    0 0 28px rgba(143, 216, 255, 0.28);
  opacity: 0;
  animation: titleParticle var(--duration) ease-in-out var(--delay) infinite;
}

.hero-copy p {
  width: min(100%, 650px);
  margin-top: 30px;
  color: rgba(226, 232, 240, 0.74);
  font-size: clamp(17px, 1.2vw, 21px);
  line-height: 1.85;
}

.hero-actions {
  gap: 16px;
  margin-top: 40px;
}

.primary-action,
.secondary-action {
  min-height: 56px;
  padding: 0 24px;
  border-radius: 999px;
}

.primary-action {
  background:
    linear-gradient(135deg, #f8fbff 0%, #dbf7ff 48%, #a9fff0 100%);
  box-shadow:
    0 20px 52px rgba(71, 240, 220, 0.22),
    inset 0 -1px rgba(7, 16, 24, 0.12);
}

.primary-action span {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(7, 16, 24, 0.08);
}

.secondary-action {
  border: 1px solid rgba(226, 232, 240, 0.16);
  background: rgba(255, 255, 255, 0.055);
  color: rgba(248, 250, 252, 0.92);
}

.secondary-action:hover {
  border-color: rgba(143, 216, 255, 0.46);
  background: rgba(143, 216, 255, 0.1);
}

.hero-proof {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  width: min(100%, 680px);
  margin-top: 44px;
}

.hero-proof-item {
  padding: 18px 18px 16px;
  border: 1px solid rgba(226, 232, 240, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.045);
  backdrop-filter: blur(16px);
}

.hero-proof-item strong,
.hero-proof-item span {
  display: block;
}

.hero-proof-item strong {
  color: #f8fafc;
  font-size: 26px;
  line-height: 1;
}

.hero-proof-item span {
  margin-top: 10px;
  color: rgba(203, 213, 225, 0.64);
  font-size: 13px;
  font-weight: 700;
}

.hero-visual {
  position: relative;
  animation: riseIn 0.72s 0.12s ease both;
}

.console-stage {
  padding: 24px;
  border-radius: 28px;
  border-color: rgba(143, 216, 255, 0.2);
  background:
    radial-gradient(circle at 10% 12%, rgba(71, 240, 220, 0.11), transparent 34%),
    radial-gradient(circle at 92% 20%, rgba(143, 216, 255, 0.09), transparent 30%),
    linear-gradient(180deg, rgba(12, 25, 44, 0.92), rgba(5, 12, 22, 0.82));
  box-shadow:
    0 42px 120px rgba(0, 0, 0, 0.48),
    0 0 0 1px rgba(255, 255, 255, 0.03),
    inset 0 1px rgba(255, 255, 255, 0.08);
  transform: translateZ(0);
  transform-origin: center;
  transition: transform 0.36s ease, box-shadow 0.36s ease;
}

.console-stage:hover {
  transform: translate3d(0, -4px, 0) scale(1.008);
  box-shadow:
    0 54px 140px rgba(0, 0, 0, 0.54),
    0 0 0 1px rgba(143, 216, 255, 0.18),
    inset 0 1px rgba(255, 255, 255, 0.1);
}

.console-stage::after {
  content: '';
  position: absolute;
  inset: -1px;
  pointer-events: none;
  border-radius: inherit;
  background: linear-gradient(115deg, transparent 20%, rgba(255, 255, 255, 0.14) 42%, transparent 58%);
  transform: translateX(-110%);
  animation: glassSweep 7s ease-in-out infinite;
}

.console-topbar {
  align-items: center;
  padding: 6px 6px 20px;
}

.console-kicker {
  color: rgba(143, 216, 255, 0.66);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.console-topbar strong {
  font-size: clamp(22px, 2vw, 30px);
  letter-spacing: -0.02em;
}

.console-tabs {
  display: inline-flex;
  gap: 6px;
  padding: 5px;
  border: 1px solid rgba(226, 232, 240, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.045);
}

.console-tabs span {
  padding: 7px 11px;
  border-radius: 999px;
  color: rgba(226, 232, 240, 0.65);
  font-size: 12px;
  font-weight: 800;
}

.console-tabs span:first-child {
  background: rgba(143, 216, 255, 0.15);
  color: #e6f8ff;
}

.console-status {
  padding: 8px 12px;
  border: 1px solid rgba(71, 240, 220, 0.14);
  border-radius: 999px;
  background: rgba(71, 240, 220, 0.08);
}

.console-flow {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: auto 1fr auto 1fr auto 1fr auto 1fr auto;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(226, 232, 240, 0.09);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
}

.console-flow span {
  color: rgba(226, 232, 240, 0.78);
  font-size: 12px;
  font-weight: 800;
}

.console-flow i {
  position: relative;
  height: 2px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
}

.console-flow i::after {
  content: '';
  position: absolute;
  inset: 0;
  width: 44%;
  border-radius: inherit;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
  animation: streamPulse 2.1s ease-in-out infinite;
}

.console-intel-row {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.console-intel-card {
  position: relative;
  overflow: hidden;
  min-height: 112px;
  padding: 18px 18px 16px;
  border: 1px solid rgba(71, 240, 220, 0.14);
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(71, 240, 220, 0.09), rgba(143, 216, 255, 0.035)),
    rgba(255, 255, 255, 0.045);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.065);
  transition: transform 0.24s ease, border-color 0.24s ease, background 0.24s ease;
}

.console-intel-card::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -12%;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: rgba(71, 240, 220, 0.1);
  filter: blur(6px);
}

.console-intel-card::after {
  content: '';
  position: absolute;
  inset: auto 18px 0;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(71, 240, 220, 0.75), transparent);
  animation: intelLine 2.8s ease-in-out infinite;
}

.console-intel-card:hover {
  transform: translateY(-4px);
  border-color: rgba(143, 216, 255, 0.34);
  background:
    linear-gradient(135deg, rgba(71, 240, 220, 0.12), rgba(143, 216, 255, 0.06)),
    rgba(255, 255, 255, 0.06);
}

.console-intel-card span,
.console-intel-card strong,
.console-intel-card p {
  position: relative;
  z-index: 1;
  display: block;
}

.console-intel-card span {
  color: rgba(143, 216, 255, 0.76);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.console-intel-card strong {
  margin-top: 9px;
  color: #f8fafc;
  font-size: 16px;
  line-height: 1.45;
}

.console-intel-card p {
  margin-top: 8px;
  color: rgba(203, 213, 225, 0.64);
  font-size: 13px;
  line-height: 1.55;
}

.console-metrics {
  grid-template-columns: minmax(180px, 1.3fr) repeat(3, minmax(130px, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.metric-card,
.capability-card,
.insight-item,
.workflow-band {
  border-radius: 20px;
  border-color: rgba(226, 232, 240, 0.1);
  background: rgba(255, 255, 255, 0.045);
}

.metric-card {
  min-height: 128px;
  padding: 18px;
  overflow: hidden;
  position: relative;
}

.metric-card::before,
.capability-card::before,
.insight-item::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at 22% 0%, rgba(143, 216, 255, 0.14), transparent 38%);
  opacity: 0;
  transition: opacity 0.28s ease;
}

.metric-card:hover::before,
.capability-card:hover::before,
.insight-item:hover::before {
  opacity: 1;
}

.metric-card span,
.metric-card strong,
.metric-card em,
.capability-card > *,
.insight-item > * {
  position: relative;
  z-index: 1;
}

.metric-card span {
  color: rgba(203, 213, 225, 0.72);
}

.metric-card strong {
  margin-top: 16px;
  font-size: 36px;
  letter-spacing: -0.05em;
}

.metric-card em {
  display: block;
  margin-top: 8px;
  color: rgba(71, 240, 220, 0.72);
  font-style: normal;
  font-size: 12px;
  font-weight: 800;
}

.risk-line {
  height: 42px;
}

.risk-line span {
  animation: barBreathe 2.8s ease-in-out infinite;
  animation-delay: calc(var(--bar-delay, 0) * 0.12s);
}

.risk-line span:nth-child(1) {
  --bar-delay: 1;
}

.risk-line span:nth-child(2) {
  --bar-delay: 2;
}

.risk-line span:nth-child(3) {
  --bar-delay: 3;
}

.risk-line span:nth-child(4) {
  --bar-delay: 4;
}

.risk-line span:nth-child(5) {
  --bar-delay: 5;
}

.capability-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.capability-card {
  position: relative;
  min-height: 190px;
  padding: 20px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.065), rgba(255, 255, 255, 0.028)),
    rgba(8, 18, 32, 0.58);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.055);
  transition:
    transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1),
    border-color 0.28s ease,
    background 0.28s ease,
    box-shadow 0.28s ease;
  animation: cardRise 0.56s ease both;
  animation-delay: calc(var(--i) * 70ms);
}

.capability-card::after {
  content: '';
  position: absolute;
  right: -38px;
  bottom: -42px;
  width: 108px;
  height: 108px;
  border-radius: 50%;
  background: rgba(71, 240, 220, 0.08);
  transition: transform 0.28s ease, opacity 0.28s ease;
}

.capability-card:hover {
  transform: translateY(-8px) scale(1.035);
  border-color: rgba(143, 216, 255, 0.44);
  background:
    linear-gradient(180deg, rgba(143, 216, 255, 0.11), rgba(71, 240, 220, 0.045)),
    rgba(8, 18, 32, 0.74);
  box-shadow:
    0 24px 54px rgba(0, 0, 0, 0.32),
    0 0 0 1px rgba(143, 216, 255, 0.08);
}

.capability-card:hover::after {
  transform: scale(1.6);
  opacity: 0.95;
}

.card-icon {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(143, 216, 255, 0.18);
  border-radius: 14px;
  background: rgba(143, 216, 255, 0.08);
}

.capability-card h3 {
  margin-bottom: 10px;
  font-size: 18px;
  letter-spacing: -0.02em;
}

.capability-card p {
  color: rgba(203, 213, 225, 0.68);
  font-size: 14px;
}

.card-state {
  align-self: flex-start;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(71, 240, 220, 0.09);
}

.insight-strip {
  gap: 18px;
  padding: 8px 0 30px;
}

.insight-item {
  position: relative;
  overflow: hidden;
  padding: 24px;
  transition: transform 0.24s ease, border-color 0.24s ease, background 0.24s ease;
}

.insight-item:hover {
  transform: translateY(-5px) scale(1.015);
  border-color: rgba(143, 216, 255, 0.36);
  background: rgba(255, 255, 255, 0.065);
}

.insight-item strong {
  margin-top: 12px;
  font-size: 34px;
  letter-spacing: -0.05em;
}

.insight-item em {
  display: block;
  margin-top: 12px;
  color: rgba(71, 240, 220, 0.72);
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
}

.flow-ribbon {
  position: relative;
  overflow: hidden;
  margin: 18px 0 32px;
  border: 1px solid rgba(226, 232, 240, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.045);
  mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
}

.marquee-track {
  display: flex;
  width: max-content;
  gap: 12px;
  padding: 12px;
  will-change: transform;
  animation: marqueeMove 42s linear infinite;
}

.marquee-track span {
  padding: 10px 18px;
  border: 1px solid rgba(143, 216, 255, 0.13);
  border-radius: 999px;
  color: rgba(226, 232, 240, 0.78);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  background: rgba(143, 216, 255, 0.055);
}

.workflow-band {
  display: grid;
  grid-template-columns: minmax(280px, 0.55fr) minmax(520px, 1fr);
  align-items: stretch;
  gap: 28px;
  margin-bottom: 0;
  padding: 28px;
  background:
    radial-gradient(circle at 18% 10%, rgba(71, 240, 220, 0.11), transparent 32%),
    rgba(255, 255, 255, 0.045);
}

.workflow-head {
  align-self: center;
}

.workflow-head span {
  color: rgba(71, 240, 220, 0.78);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.workflow-head strong {
  display: block;
  max-width: 440px;
  font-size: clamp(24px, 2.4vw, 42px);
  line-height: 1.12;
  letter-spacing: -0.05em;
}

.workflow-steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.workflow-steps article {
  min-height: 178px;
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, 0.1);
  border-radius: 18px;
  background: rgba(6, 13, 24, 0.46);
  transition: transform 0.24s ease, border-color 0.24s ease, background 0.24s ease;
}

.workflow-steps article:hover {
  transform: translateY(-5px);
  border-color: rgba(143, 216, 255, 0.32);
  background: rgba(143, 216, 255, 0.075);
}

.workflow-steps em {
  display: inline-flex;
  color: rgba(71, 240, 220, 0.78);
  font-size: 12px;
  font-style: normal;
  font-weight: 900;
}

.workflow-steps strong {
  display: block;
  margin-top: 24px;
  color: #f8fafc;
  font-size: 17px;
}

.workflow-steps p {
  margin-top: 10px;
  color: rgba(203, 213, 225, 0.66);
  font-size: 13px;
  line-height: 1.65;
}

.auth-panel {
  border-radius: 28px 0 0 28px;
}

@keyframes auroraDrift {
  from {
    transform: translate3d(-1.5%, -1%, 0) scale(1);
  }

  to {
    transform: translate3d(1.5%, 1.5%, 0) scale(1.04);
  }
}

@keyframes glowPulse {
  from {
    opacity: 0.52;
    transform: translateY(-8px) scale(1);
  }

  to {
    opacity: 0.82;
    transform: translateY(10px) scale(1.05);
  }
}

@keyframes riseIn {
  from {
    opacity: 0;
    transform: translateY(24px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes cardRise {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes titleHalo {
  from {
    opacity: 0.48;
    transform: translate3d(-1.5%, -1%, 0) scale(0.98);
  }

  to {
    opacity: 0.9;
    transform: translate3d(1.5%, 1%, 0) scale(1.04);
  }
}

@keyframes scanLines {
  from {
    transform: translateX(-4%);
  }

  to {
    transform: translateX(4%);
  }
}

@keyframes titleParticle {
  0% {
    opacity: 0;
    transform: translate3d(-8px, 10px, 0) scale(0.45);
  }

  28%,
  68% {
    opacity: 0.9;
  }

  100% {
    opacity: 0;
    transform: translate3d(12px, -18px, 0) scale(1.16);
  }
}

@keyframes livePulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 12px rgba(71, 240, 220, 0.7);
  }

  50% {
    transform: scale(1.35);
    box-shadow: 0 0 22px rgba(71, 240, 220, 1);
  }
}

@keyframes glassSweep {
  0%,
  45% {
    transform: translateX(-115%);
  }

  68%,
  100% {
    transform: translateX(115%);
  }
}

@keyframes streamPulse {
  from {
    transform: translateX(-100%);
  }

  to {
    transform: translateX(240%);
  }
}

@keyframes intelLine {
  0%,
  100% {
    opacity: 0.24;
    transform: scaleX(0.35);
  }

  50% {
    opacity: 0.82;
    transform: scaleX(1);
  }
}

@keyframes barBreathe {
  0%,
  100% {
    filter: brightness(0.9);
    transform: scaleY(0.88);
  }

  50% {
    filter: brightness(1.3);
    transform: scaleY(1);
  }
}

@keyframes floatSoft {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-12px);
  }
}

@keyframes marqueeMove {
  from {
    transform: translateX(0);
  }

  to {
    transform: translateX(-50%);
  }
}

@media (max-width: 1380px) {
  .section-locator {
    right: 18px;
  }

  .section-locator a {
    width: 44px;
    grid-template-columns: 28px;
    padding: 8px;
    color: transparent;
  }

  .section-locator span {
    color: rgba(143, 216, 255, 0.9);
  }

  .hero-section {
    grid-template-columns: minmax(390px, 0.9fr) minmax(560px, 1.1fr);
    gap: 54px;
  }

  .capability-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .capability-card {
    min-height: 172px;
  }
}

@media (max-width: 1180px) {
  .site-header {
    min-height: 70px;
  }

  .section-locator {
    top: auto;
    right: 50%;
    bottom: 18px;
    grid-auto-flow: column;
    transform: translateX(50%);
  }

  .section-locator a {
    width: 44px;
  }

  .section-locator a::before {
    content: none;
  }

  .section-locator a:hover,
  .section-locator a:focus-visible {
    transform: translateY(-4px);
  }

  .hero-section {
    grid-template-columns: 1fr;
    min-height: auto;
    padding-top: 72px;
  }

  .hero-copy {
    max-width: 900px;
  }

  .hero-visual {
    width: min(100%, 920px);
  }

  .console-stage {
    transform: none;
  }

  .workflow-band {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 920px) {
  .site-header,
  .landing-shell {
    width: 100%;
  }

  .site-header {
    padding-inline: 18px;
  }

  .landing-shell {
    width: min(100% - 36px, 1680px);
  }

  .console-tabs {
    display: none;
  }

  .console-topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .console-flow {
    grid-template-columns: 1fr;
  }

  .console-flow i {
    display: none;
  }

  .hero-proof,
  .console-metrics,
  .console-intel-row,
  .capability-grid,
  .insight-strip,
  .workflow-steps {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .auth-page {
    --page-gutter: 18px;
  }

  .site-header {
    min-height: 66px;
  }

  .header-actions {
    gap: 8px;
  }

  .login-entry {
    padding-inline: 14px;
  }

  .hero-section {
    padding-top: 54px;
  }

  .hero-copy h1 {
    font-size: clamp(44px, 13vw, 64px);
  }

  .hero-copy p {
    font-size: 16px;
  }

  .console-stage {
    padding: 18px;
    border-radius: 22px;
  }

  .workflow-band {
    padding: 20px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-page *,
  .auth-page *::before,
  .auth-page *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}
</style>
