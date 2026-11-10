import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AxiosError } from 'axios'
import { createPinia, setActivePinia } from 'pinia'
import { createHttpError } from '@/__tests__/factories'
import { checkIsUserLogged, logoutUser, logUser } from '@/api/generated/endpoints/auth/auth'
import { SessionExpiredError } from '@/api/sessionExpiry'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/api/generated/endpoints/auth/auth', () => ({
  checkIsUserLogged: vi.fn(),
  logoutUser: vi.fn(),
  logUser: vi.fn(),
}))

describe('auth store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it.each([true, false])(
    'checkIsLogged restores the session of a logged user (isAdmin: %s)',
    async (isAdmin) => {
      vi.mocked(checkIsUserLogged).mockResolvedValueOnce({ isAdmin })
      const store = useAuthStore()

      await store.checkIsLogged()

      expect(store.isUserLogged).toBe(true)
      expect(store.isAdmin).toBe(isAdmin)
    },
  )

  it('checkIsLogged marks the user as logged out on 401', async () => {
    vi.mocked(checkIsUserLogged).mockRejectedValueOnce(createHttpError(401))
    const store = useAuthStore()
    store.isUserLogged = true
    store.isAdmin = true

    await store.checkIsLogged()

    expect(store.isUserLogged).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('checkIsLogged marks the user as logged out when the session expired', async () => {
    vi.mocked(checkIsUserLogged).mockRejectedValueOnce(new SessionExpiredError('Session expired'))
    const store = useAuthStore()

    await store.checkIsLogged()

    expect(store.isUserLogged).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('checkIsLogged rethrows errors other than 401', async () => {
    const error = createHttpError(500)
    vi.mocked(checkIsUserLogged).mockRejectedValueOnce(error)
    const store = useAuthStore()

    await expect(store.checkIsLogged()).rejects.toBe(error)
  })

  it('login stores the session and admin flag', async () => {
    vi.mocked(checkIsUserLogged).mockResolvedValueOnce({ isAdmin: true })
    const store = useAuthStore()

    await store.login('user', 'password')

    expect(logUser).toHaveBeenCalledWith({
      grant_type: 'password',
      username: 'user',
      password: 'password',
    })
    expect(store.isUserLogged).toBe(true)
    expect(store.isAdmin).toBe(true)
  })

  it('login of a regular user does not grant admin rights', async () => {
    vi.mocked(checkIsUserLogged).mockResolvedValueOnce({ isAdmin: false })
    const store = useAuthStore()

    await store.login('user', 'password')

    expect(store.isUserLogged).toBe(true)
    expect(store.isAdmin).toBe(false)
  })

  it('login does not grant admin rights when the new session cannot be read', async () => {
    vi.mocked(checkIsUserLogged).mockRejectedValueOnce(createHttpError(401))
    const store = useAuthStore()

    await store.login('user', 'password')

    expect(store.isAdmin).toBe(false)
  })

  it('login keeps the user logged out when the credentials are rejected', async () => {
    const error = createHttpError(401)
    vi.mocked(logUser).mockRejectedValueOnce(error)
    const store = useAuthStore()

    await expect(store.login('user', 'wrong')).rejects.toBe(error)

    expect(store.isUserLogged).toBe(false)
    expect(checkIsUserLogged).not.toHaveBeenCalled()
  })

  it('logout resets the session', async () => {
    vi.mocked(checkIsUserLogged).mockResolvedValueOnce({ isAdmin: true })
    const store = useAuthStore()
    await store.login('user', 'password')

    await store.logout()

    expect(logoutUser).toHaveBeenCalledOnce()
    expect(store.isUserLogged).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('logout resets the session even when the request fails', async () => {
    vi.mocked(checkIsUserLogged).mockResolvedValueOnce({ isAdmin: true })
    vi.mocked(logoutUser).mockRejectedValueOnce(createHttpError(500))
    const store = useAuthStore()
    await store.login('user', 'password')

    await expect(store.logout()).rejects.toBeInstanceOf(AxiosError)

    expect(store.isUserLogged).toBe(false)
    expect(store.isAdmin).toBe(false)
  })
})
