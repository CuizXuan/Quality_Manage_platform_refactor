import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Auth.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/cases',
    name: 'Cases',
    component: () => import('../views/CaseManagement.vue'),
  },
  {
    path: '/scenarios',
    name: 'Scenarios',
    component: () => import('../views/ScenarioEditor.vue'),
  },
  {
    path: '/environments',
    name: 'Environments',
    component: () => import('../views/EnvironmentManage.vue'),
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/ExecutionHistory.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
  },
  {
    path: '/shortcuts',
    name: 'Shortcuts',
    component: () => import('../views/Shortcuts.vue'),
  },
  {
    path: '/datasets',
    name: 'Datasets',
    component: () => import('../views/DataDrive/DatasetList.vue'),
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: () => import('../views/Schedule/ScheduleList.vue'),
  },
  {
    path: '/mock-rules',
    name: 'MockRules',
    component: () => import('../views/Mock/MockRuleList.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/Report/ReportList.vue'),
  },
  {
    path: '/repositories',
    name: 'Repositories',
    component: () => import('../views/CodeQuality/RepositoryList.vue'),
  },
  {
    path: '/coverage',
    name: 'Coverage',
    component: () => import('../views/CodeQuality/CoverageDashboard.vue'),
  },
  {
    path: '/defects',
    name: 'Defects',
    component: () => import('../views/Defect/DefectBoard.vue'),
  },
  {
    path: '/quality-gates',
    name: 'QualityGates',
    component: () => import('../views/QualityGate/GateList.vue'),
  },
  {
    path: '/integration/defect-systems',
    name: 'DefectSystems',
    component: () => import('../views/Integration/DefectSystemConfig.vue'),
  },
  // Phase 4 新增路由
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/ProjectManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'UserManage',
    component: () => import('../views/UserManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/team',
    name: 'TeamManage',
    component: () => import('../views/TeamManage.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 4 模块二：资产共享
  {
    path: '/assets',
    name: 'AssetCenter',
    component: () => import('../views/AssetCenter.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 4 模块三：智能分析
  {
    path: '/ai-analysis',
    name: 'AIAnalysis',
    component: () => import('../views/AIAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 4 模块四：质量大盘
  {
    path: '/quality-dashboard',
    name: 'QualityDashboard',
    component: () => import('../views/QualityDashboard.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 5 AI 实验室
  {
    path: '/ai-lab',
    name: 'AILab',
    component: () => import('../views/AIStudio.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 5 全链路压测
  {
    path: '/load-test',
    name: 'TrafficLoadTest',
    component: () => import('../views/TrafficLoadTest.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 5 混沌工程
  {
    path: '/chaos',
    name: 'ChaosStudio',
    component: () => import('../views/ChaosStudio.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 5 测试数据工厂
  {
    path: '/test-data',
    name: 'TestDataFactory',
    component: () => import('../views/TestDataFactory.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 5 插件市场
  {
    path: '/marketplace',
    name: 'Marketplace',
    component: () => import('../views/Marketplace.vue'),
    meta: { requiresAuth: true }
  },
  // Phase 5 企业审计
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('../views/AuditLog.vue'),
    meta: { requiresAuth: true }
  },
  // 系统管理
  {
    path: '/menu-manage',
    name: 'MenuManage',
    component: () => import('../views/MenuManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-model-config',
    name: 'AIModelConfig',
    component: () => import('../views/AIModelConfig.vue'),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !authStore.isAuthenticated) {
    // 需要认证但未登录，跳转到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
