import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import LoginPage from '../LoginPage.vue'
import { createTestApp } from '@/__tests__/app'
import { createHttpError, createNetworkError } from '@/__tests__/factories'
import { checkIsUserLogged, logUser } from '@/api/generated/endpoints/auth/auth'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/api/generated/endpoints/auth/auth')

async function mountPage(path = '/auth/login') {
  const { router, global } = await createTestApp(path)
  const wrapper = mount(LoginPage, { global })
  return { router, wrapper }
}

async function submitCredentials(
  wrapper: Awaited<ReturnType<typeof mountPage>>['wrapper'],
  username: string,
  password: string,
) {
  await wrapper.find('#username').setValue(username)
  await wrapper.find('#password').setValue(password)
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(checkIsUserLogged).mockResolvedValue({ isAdmin: false })
  })

  it('logs the user in and opens the main page', async () => {
    const { router, wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

    expect(logUser).toHaveBeenCalledExactlyOnceWith({
      grant_type: 'password',
      username: 'jan',
      password: 'StrongPassword12;',
    })
    expect(useAuthStore().isUserLogged).toBe(true)
    expect(router.currentRoute.value.fullPath).toBe('/')
  })

  it('returns to the page that required logging in', async () => {
    const redirect = '/user/regulations/r-1/documents?query=urlop'
    const { router, wrapper } = await mountPage(
      `/auth/login?redirect=${encodeURIComponent(redirect)}`,
    )

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

    expect(router.currentRoute.value.fullPath).toBe(redirect)
  })

  it.each(['https://evil.example.com', '//evil.example.com', 'user/cases/case-1'])(
    'opens the main page instead of the unsafe redirect %s',
    async (redirect) => {
      const { router, wrapper } = await mountPage(
        `/auth/login?redirect=${encodeURIComponent(redirect)}`,
      )

      await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

      expect(router.currentRoute.value.fullPath).toBe('/')
    },
  )

  it('informs about wrong credentials and stays on the login page', async () => {
    vi.mocked(logUser).mockRejectedValueOnce(createHttpError(401))
    const { router, wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', 'wrong')

    expect(wrapper.find('.el-alert').text()).toBe('Nieprawidłowa nazwa użytkownika lub hasło.')
    expect(useAuthStore().isUserLogged).toBe(false)
    expect(router.currentRoute.value.name).toBe('LoginPage')
  })

  it('informs about a connection problem', async () => {
    vi.mocked(logUser).mockRejectedValueOnce(createNetworkError())
    const { wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

    expect(wrapper.find('.el-alert').text()).toBe(
      'Nie można połączyć się z serwerem. Sprawdź połączenie sieciowe.',
    )
  })

  it('clears the previous error after a successful attempt', async () => {
    vi.mocked(logUser).mockRejectedValueOnce(createHttpError(401))
    const { wrapper } = await mountPage()
    await submitCredentials(wrapper, 'jan', 'wrong')

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

    expect(wrapper.find('.el-alert').exists()).toBe(false)
  })

  it.each([
    ['', 'StrongPassword12;'],
    ['jan', ''],
  ])('requires both the username and the password', async (username, password) => {
    const { wrapper } = await mountPage()

    await submitCredentials(wrapper, username, password)

    expect(wrapper.find('.el-alert').text()).toBe('Wypełnij wszystkie pola.')
    expect(logUser).not.toHaveBeenCalled()
  })

  it('shows the form as busy until the login attempt ends', async () => {
    let finishLogin: ((value: unknown) => void) | undefined
    vi.mocked(logUser).mockImplementationOnce(
      () => new Promise((resolve) => (finishLogin = resolve)),
    )
    const { wrapper } = await mountPage()
    const submitButton = wrapper.find('button[type="submit"]')
    expect(submitButton.classes()).not.toContain('is-loading')

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')
    expect(submitButton.classes()).toContain('is-loading')

    finishLogin?.(undefined)
    await flushPromises()
    expect(submitButton.classes()).not.toContain('is-loading')
  })

  it('links to the registration page', async () => {
    const { router, wrapper } = await mountPage()

    await wrapper.find('.auth-link a').trigger('click')
    await flushPromises()

    expect(wrapper.find('.auth-link a').text()).toBe('Załóż konto')
    expect(router.currentRoute.value.name).toBe('RegisterPage')
  })
})
