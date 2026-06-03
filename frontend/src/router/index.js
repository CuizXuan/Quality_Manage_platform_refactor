import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Auth.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('../app/AppShell.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/platform/Dashboard.vue'),
      },
      {
        path: '/terminal',
        name: 'Terminal',
        component: () => import('../views/terminal/Terminal.vue'),
      },
      {
        path: '/api-assets',
        name: 'ApiAssetCenter',
        component: () => import('../views/apiAsset/ApiAssetCenter.vue'),
      },
      {
        path: '/api-assets/import-jobs',
        name: 'ImportJobs',
        component: () => import('../views/apiAsset/ImportJobs.vue'),
      },
      {
        path: '/case',
        name: 'CaseManagement',
        component: () => import('../views/case/CaseManagement.vue'),
      },
      {
        path: '/scenario',
        name: 'ScenarioList',
        component: () => import('../views/scenario/ScenarioList.vue'),
      },
      {
        path: '/scenario/executions',
        name: 'ExecutionHistory',
        component: () => import('../views/scenario/ExecutionHistory.vue'),
      },
      {
        path: '/scenario/executions/:id',
        name: 'ExecutionDetail',
        component: () => import('../views/scenario/ExecutionDetail.vue'),
      },
      {
        path: '/executions',
        name: 'ExecutionCenter',
        component: () => import('../views/execution/ExecutionCenter.vue'),
      },
      {
        path: '/executions/:id',
        name: 'ExecutionDetailView',
        component: () => import('../views/execution/ExecutionDetailView.vue'),
      },
      {
        path: '/test-plans',
        name: 'TestPlanList',
        component: () => import('../views/testPlan/TestPlanList.vue'),
      },
      {
        path: '/test-plans/:id',
        name: 'TestPlanDetail',
        component: () => import('../views/testPlan/TestPlanDetail.vue'),
      },
      {
        path: '/test-plan-runs',
        name: 'TestPlanRuns',
        component: () => import('../views/testPlan/TestPlanRuns.vue'),
      },
      {
        path: '/ai/workbench',
        name: 'AIWorkbench',
        component: () => import('../views/ai/AIWorkbench.vue'),
      },
      {
        path: '/ai/config',
        name: 'AIModelConfig',
        component: () => import('../views/ai/AIModelConfig.vue'),
      },
      {
        path: '/ai/templates',
        name: 'AIPromptTemplates',
        component: () => import('../views/ai/AIPromptTemplates.vue'),
      },
      {
        path: '/ai/variant-generator',
        name: 'VariantGenerator',
        component: () => import('../views/ai/VariantGenerator.vue'),
      },
      {
        path: '/ai/assertion-generator',
        name: 'AssertionGenerator',
        component: () => import('../views/ai/AssertionGenerator.vue'),
      },
      {
        path: '/ai/failure-analyzer',
        name: 'FailureAnalyzer',
        component: () => import('../views/ai/FailureAnalyzer.vue'),
      },
      {
        path: '/ai/report-summarizer',
        name: 'ReportSummarizer',
        component: () => import('../views/ai/ReportSummarizer.vue'),
      },
      {
        path: '/ai/suggestion-history',
        name: 'SuggestionHistory',
        component: () => import('../views/ai/SuggestionHistory.vue'),
      },
      {
        path: '/quality-analytics',
        name: 'QualityAnalytics',
        component: () => import('../views/qualityAnalytics/QualityAnalytics.vue'),
      },
      {
        path: '/report',
        name: 'ReportList',
        component: () => import('../views/report/ReportList.vue'),
      },
      {
        path: '/report/:id',
        name: 'ReportDetail',
        component: () => import('../views/report/ReportDetail.vue'),
      },
      {
        path: '/defect',
        name: 'DefectList',
        component: () => import('../views/report/DefectList.vue'),
      },
      {
        path: '/quality-gate',
        name: 'QualityGate',
        component: () => import('../views/report/QualityGate.vue'),
      },
      {
        path: '/docgen',
        name: 'DocGenerationCenter',
        component: () => import('../views/docgen/DocGenerationCenter.vue'),
        redirect: '/docgen/tasks',
        children: [
          { path: '/docgen/tasks', name: 'DocGenTasks', component: () => import('../views/docgen/DocGenTasks.vue') },
          { path: '/docgen/rules', name: 'DocGenRules', component: () => import('../views/docgen/DocGenRules.vue') },
          { path: '/docgen/templates', name: 'DocGenTemplates', component: () => import('../views/docgen/DocGenTemplates.vue') },
          { path: '/docgen/generate', name: 'DocGenGenerate', component: () => import('../views/docgen/DocGenGenerate.vue') },
        ],
      },
      {
        path: '/foundation/projects',
        name: 'ProjectManagement',
        component: () => import('../views/foundation/ProjectManagement.vue'),
      },
      {
        path: '/foundation/requirements',
        name: 'RequirementManagement',
        component: () => import('../views/foundation/RequirementManagement.vue'),
      },
      {
        path: '/system/users',
        name: 'SystemUsers',
        component: () => import('../views/platform/UserManagement.vue'),
      },
      {
        path: '/system/roles',
        name: 'SystemRoles',
        component: () => import('../views/platform/RoleManagement.vue'),
      },
      {
        path: '/system/organizations',
        name: 'SystemOrganizations',
        component: () => import('../views/platform/OrganizationManagement.vue'),
      },
      {
        path: '/system/menus',
        name: 'SystemMenus',
        component: () => import('../views/platform/MenuManagement.vue'),
      },
      {
        path: '/system/dictionaries',
        name: 'SystemDictionaries',
        component: () => import('../views/platform/DictionaryManagement.vue'),
      },
      {
        path: '/system/logs',
        name: 'SystemLogs',
        component: () => import('../views/platform/LogManagement.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth === false) return true
  if (!authStore.isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (!authStore.user) {
    await authStore.fetchUserInfo()
  }
  return true
})

export default router
