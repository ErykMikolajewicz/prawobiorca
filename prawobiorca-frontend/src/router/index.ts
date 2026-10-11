import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { setPageMeta } from '@/utils/pageMeta'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    description?: string
  }
}

const SearchPage = () => import('@/pages/SearchPage.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'MainPage',
      component: () => import('@/pages/MainPage.vue'),
      meta: {
        title: 'Prawobiorca – wyszukiwarka aktów prawnych i generator wniosków',
        description:
          'Przeszukuj regulaminy i akty prawne uczelni z pomocą AI, a na ich podstawie generuj wnioski. Prawobiorca pomoże Ci załatwić sprawy na uczelni.',
      },
    },
    {
      path: '/features',
      name: 'FeaturesPage',
      component: () => import('@/pages/FeaturesPage.vue'),
      meta: {
        title: 'Funkcje dla zalogowanych – Prawobiorca',
        description:
          'Załóż konto w Prawobiorcy, aby tworzyć sprawy, przypinać do nich przepisy, generować wnioski z szablonów i przeszukiwać własne regulacje.',
      },
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
      path: '/admin/application-templates',
      name: 'ApplicationTemplatesPage',
      component: () => import('@/pages/ApplicationTemplatesPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/application-templates/:id',
      name: 'ApplicationTemplatePage',
      component: () => import('@/pages/ApplicationTemplatePage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/organizations',
      name: 'OrganizationsPage',
      component: () => import('@/pages/OrganizationsPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'MainPage' },
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isUserLogged) {
    return { name: 'LoginPage', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'MainPage' }
  }
})

router.afterEach((to) => {
  setPageMeta(to.meta.title, to.meta.description)
})

export default router
