import { createRouter, createWebHistory } from 'vue-router'
import MainPage from '@/pages/MainPage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import RegisterPage from '@/pages/RegisterPage.vue'
import SearchPage from '@/pages/SearchPage.vue'
import CasePage from '@/pages/CasePage.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'MainPage',
      component: MainPage,
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
      component: LoginPage,
    },
    {
      path: '/accounts/register',
      name: 'RegisterPage',
      component: RegisterPage,
    },
    {
      path: '/user/cases/:id',
      name: 'CasePage',
      component: CasePage,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !useAuthStore().isUserLogged) {
    return { name: 'LoginPage' }
  }
})

export default router
