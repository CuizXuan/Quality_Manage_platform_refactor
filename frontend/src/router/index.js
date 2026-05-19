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
        path: 'terminal',
        name: 'Terminal',
        component: () => import('../views/terminal/Terminal.vue'),
      },
      {
        path: 'case',
        name: 'Case',
        component: () => import('../views/case/Case.vue'),
        redirect: '/case/api',
        children: [
          {
            path: 'functional',
            name: 'FunctionalCases',
            component: () => import('../views/case/functional/FunctionalCase.vue'),
          },
          {
            path: 'api',
            name: 'ApiCases',
            component: () => import('../views/case/api/ApiCase.vue'),
          },
        ],
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

