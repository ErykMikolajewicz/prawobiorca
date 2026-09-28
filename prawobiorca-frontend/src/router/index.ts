import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const SearchPage = () => import('@/pages/SearchPage.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'MainPage',
      component: () => import('@/pages/MainPage.vue'),
    },
    {
      path: '/regulations/:regulationId/documents',
      name: 'SearchPublicRegulation',
      component: SearchPage,
    },
    {
      path: '/user/regulations/:regulationId/documents',
      name: 'SearchUserRegulation',
      component: SearchPage,
      meta: { requiresAuth: true },
    },
    {
      path: '/auth/login',
      name: 'LoginPage',
      component: () => import('@/pages/LoginPage.vue'),
    },
    {
      path: '/accounts/register',
      name: 'RegisterPage',
      component: () => import('@/pages/RegisterPage.vue'),
    },
    {
      path: '/user/cases/:id',
      name: 'CasePage',
      component: () => import('@/pages/CasePage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'MainPage' },
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !useAuthStore().isUserLogged) {
    return { name: 'LoginPage', query: { redirect: to.fullPath } }
  }
})

export default router
