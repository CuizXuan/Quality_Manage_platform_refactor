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
        path: 'system/users',
        name: 'SystemUsers',
        component: () => import('../views/platform/UserManagement.vue'),
      },
      {
        path: 'system/roles',
        name: 'SystemRoles',
        component: () => import('../views/platform/RoleManagement.vue'),
      },
      {
        path: 'system/organizations',
        name: 'SystemOrganizations',
        component: () => import('../views/platform/OrganizationManagement.vue'),
      },
      {
        path: 'system/menus',
        name: 'SystemMenus',
        component: () => import('../views/platform/MenuManagement.vue'),
      },
      {
        path: 'system/dictionaries',
        name: 'SystemDictionaries',
        component: () => import('../views/platform/DictionaryManagement.vue'),
      },
      {
        path: 'terminal',
        name: 'Terminal',
        component: () => import('../views/terminal/Terminal.vue'),
      },
      {
        path: 'case',
        name: 'CaseManagement',
        component: () => import('../views/case/CaseManagement.vue'),
      },
      {
        path: 'scenario',
        name: 'ScenarioList',
        component: () => import('../views/scenario/ScenarioList.vue'),
      },
      {
        path: 'scenario/executions',
        name: 'ExecutionHistory',
        component: () => import('../views/scenario/ExecutionHistory.vue'),
      },
      {
        path: 'scenario/executions/:id',
        name: 'ExecutionDetail',
        component: () => import('../views/scenario/ExecutionDetail.vue'),
      },
      {
        path: 'scenario/:id',
        name: 'ScenarioDetail',
        component: () => import('../views/scenario/ScenarioDetail.vue'),
      },
      {
        path: 'report',
        name: 'ReportList',
        component: () => import('../views/report/ReportList.vue'),
      },
      {
        path: 'report/:id',
        name: 'ReportDetail',
        component: () => import('../views/report/ReportDetail.vue'),
      },
      {
        path: 'defect',
        name: 'DefectList',
        component: () => import('../views/report/DefectList.vue'),
      },
      {
        path: 'quality-gate',
        name: 'QualityGate',
        component: () => import('../views/report/QualityGate.vue'),
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