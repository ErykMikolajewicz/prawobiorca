import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const emptyPage = vi.hoisted(() => ({ default: { render: () => null } }))

vi.mock('@/pages/MainPage.vue', () => emptyPage)
vi.mock('@/pages/FeaturesPage.vue', () => emptyPage)
vi.mock('@/pages/SearchPage.vue', () => emptyPage)
vi.mock('@/pages/LoginPage.vue', () => emptyPage)
vi.mock('@/pages/RegisterPage.vue', () => emptyPage)
vi.mock('@/pages/CasePage.vue', () => emptyPage)
vi.mock('@/pages/ApplicationTemplatesPage.vue', () => emptyPage)
vi.mock('@/pages/ApplicationTemplatePage.vue', () => emptyPage)
vi.mock('@/pages/OrganizationsPage.vue', () => emptyPage)

const DEFAULT_TITLE = 'Prawobiorca'

function logIn(isAdmin = false) {
  const authStore = useAuthStore()
  authStore.isUserLogged = true
  authStore.isAdmin = isAdmin
}

describe('router', () => {
  let router: Router

  beforeAll(async () => {
    document.title = DEFAULT_TITLE
    router = (await import('@/router')).default
  })

  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it.each(['/', '/features', '/auth/login', '/accounts/register', '/regulations/r-1/documents'])(
    'lets a guest open %s',
    async (path) => {
      await router.push(path)

      expect(router.currentRoute.value.fullPath).toBe(path)
    },
  )

  it.each([
    '/user/cases/case-1',
    '/user/regulations/r-1/documents?query=urlop',
    '/admin/application-templates',
    '/admin/application-templates/template-1',
    '/admin/organizations',
  ])('redirects a guest from %s to the login page and remembers the path', async (path) => {
    await router.push(path)

    expect(router.currentRoute.value.name).toBe('LoginPage')
    expect(router.currentRoute.value.query).toEqual({ redirect: path })
  })

  it.each(['/user/cases/case-1', '/user/regulations/r-1/documents'])(
    'lets a logged user open %s',
    async (path) => {
      logIn()

      await router.push(path)

      expect(router.currentRoute.value.fullPath).toBe(path)
    },
  )

  it.each([
    '/admin/application-templates',
    '/admin/application-templates/template-1',
    '/admin/organizations',
  ])('redirects a user without admin rights from %s to the main page', async (path) => {
    logIn()

    await router.push(path)

    expect(router.currentRoute.value.name).toBe('MainPage')
  })

  it.each([
    ['/admin/application-templates', 'ApplicationTemplatesPage'],
    ['/admin/application-templates/template-1', 'ApplicationTemplatePage'],
    ['/admin/organizations', 'OrganizationsPage'],
  ])('lets an administrator open %s', async (path, routeName) => {
    logIn(true)

    await router.push(path)

    expect(router.currentRoute.value.name).toBe(routeName)
  })

  it('redirects an unknown path to the main page', async () => {
    await router.push('/unknown/path')

    expect(router.currentRoute.value.name).toBe('MainPage')
  })

  it('sets the title of an indexed page and restores the default one on other pages', async () => {
    await router.push('/features')
    expect(document.title).toBe('Funkcje dla zalogowanych – Prawobiorca')

    await router.push('/auth/login')
    expect(document.title).toBe(DEFAULT_TITLE)
  })
})
