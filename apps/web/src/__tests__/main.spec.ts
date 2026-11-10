import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { findButton, page, shownMessages } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import type { CurrentUser } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/auth/auth')
vi.mock('@/api/generated/endpoints/cases/cases')
vi.mock('@/api/generated/endpoints/organizations/organizations')
vi.mock('@/api/generated/endpoints/regulations/regulations')

async function startApp(currentUser: Promise<CurrentUser>) {
  vi.resetModules()
  document.body.innerHTML = '<div id="app"></div>'

  const { checkIsUserLogged } = await import('@/api/generated/endpoints/auth/auth')
  const { getCasesList } = await import('@/api/generated/endpoints/cases/cases')
  const { getOrganizations } = await import('@/api/generated/endpoints/organizations/organizations')
  const { getRegulations } = await import('@/api/generated/endpoints/regulations/regulations')
  vi.mocked(checkIsUserLogged).mockReturnValue(currentUser)
  vi.mocked(getCasesList).mockResolvedValue([])
  vi.mocked(getOrganizations).mockResolvedValue([])
  vi.mocked(getRegulations).mockResolvedValue([])

  await import('@/main')
  const { default: router } = await import('@/router')
  await router.isReady()
  await flushPromises()

  const { useAuthStore } = await import('@/stores/auth')
  const { notifySessionExpired } = await import('@/api/sessionExpiry')
  return { router, authStore: useAuthStore(), notifySessionExpired }
}

describe('application start', { timeout: 30_000 }, () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
    vi.stubGlobal(
      'matchMedia',
      vi.fn(() => ({ matches: false, addEventListener: vi.fn() })),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    document.documentElement.classList.remove('dark')
  })

  it('restores the session before showing the page', async () => {
    const { authStore } = await startApp(Promise.resolve({ isAdmin: false }))

    expect(authStore.isUserLogged).toBe(true)
    expect(page().text()).toContain('Regulacje użytkownika')
    expect(page().find('.login-cta-banner').exists()).toBe(false)
    expect(findButton('Szukaj')).toBeDefined()
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(page().find('.app-top-bar').exists()).toBe(false)
  })

  it('follows the dark system theme and the mobile viewport', async () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn(() => ({ matches: true, addEventListener: vi.fn() })),
    )

    await startApp(Promise.resolve({ isAdmin: false }))

    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(page().find('.app-top-bar').exists()).toBe(true)
  })

  it('shows the page to a guest when there is no session', async () => {
    const { authStore } = await startApp(Promise.reject(createHttpError(401)))

    expect(authStore.isUserLogged).toBe(false)
    expect(page().find('.login-cta-banner').exists()).toBe(true)
    expect(shownMessages('error')).toEqual([])
  })

  it('reports a session that could not be checked and still shows the page', async () => {
    await startApp(Promise.reject(createHttpError(500)))

    expect(shownMessages('error')).toEqual([
      'Wystąpił błąd po stronie serwera. Spróbuj ponownie później.',
    ])
    expect(page().text()).toContain('Publiczne regulacje')
  })

  it('asks to log in again when the session expires and remembers the page', async () => {
    const { router, authStore, notifySessionExpired } = await startApp(
      Promise.resolve({ isAdmin: true }),
    )
    await router.push('/features')

    notifySessionExpired()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('LoginPage'), {
      timeout: 10_000,
    })

    expect(authStore.isUserLogged).toBe(false)
    expect(authStore.isAdmin).toBe(false)
    expect(shownMessages('error')).toEqual(['Sesja wygasła. Zaloguj się ponownie.'])
    expect(router.currentRoute.value.query).toEqual({ redirect: '/features' })
  })

  it('does not disturb a guest when a refresh of the session fails', async () => {
    const { router, notifySessionExpired } = await startApp(Promise.reject(createHttpError(401)))
    await router.push('/features')

    notifySessionExpired()
    await flushPromises()

    expect(shownMessages('error')).toEqual([])
    expect(router.currentRoute.value.name).toBe('FeaturesPage')
  })
})
