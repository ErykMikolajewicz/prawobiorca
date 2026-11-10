import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import RegisterPage from '../RegisterPage.vue'
import { createTestApp } from '@/__tests__/app'
import { shownMessages } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import { createAccount } from '@/api/generated/endpoints/account/account'

vi.mock('@/api/generated/endpoints/account/account')

async function mountPage() {
  const { router, global } = await createTestApp('/accounts/register')
  const wrapper = mount(RegisterPage, { global })
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

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates the account and opens the login page', async () => {
    const { router, wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

    expect(createAccount).toHaveBeenCalledExactlyOnceWith({
      username: 'jan',
      password: 'StrongPassword12;',
    })
    expect(shownMessages('success')).toEqual([
      'Rejestracja przebiegła pomyślnie. Możesz się teraz zalogować.',
    ])
    expect(router.currentRoute.value.name).toBe('LoginPage')
  })

  it('informs that the username is taken and stays on the page', async () => {
    vi.mocked(createAccount).mockRejectedValueOnce(createHttpError(409))
    const { router, wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', 'StrongPassword12;')

    expect(wrapper.find('.el-alert').text()).toBe('Nazwa użytkownika jest już zajęta.')
    expect(shownMessages('success')).toEqual([])
    expect(router.currentRoute.value.name).toBe('RegisterPage')
  })

  it('informs about rejected data', async () => {
    vi.mocked(createAccount).mockRejectedValueOnce(createHttpError(422))
    const { wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', 'weak')

    expect(wrapper.find('.el-alert').text()).toBe(
      'Nie udało się wykonać operacji. Sprawdź dane i spróbuj ponownie.',
    )
  })

  it('does not create an account without a password', async () => {
    const { wrapper } = await mountPage()

    await submitCredentials(wrapper, 'jan', '')

    expect(wrapper.find('.el-alert').text()).toBe('Wypełnij wszystkie pola.')
    expect(createAccount).not.toHaveBeenCalled()
  })

  it('links to the login page', async () => {
    const { router, wrapper } = await mountPage()

    await wrapper.find('.auth-link a').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('LoginPage')
  })
})
