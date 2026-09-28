import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { createPinia, setActivePinia } from 'pinia'
import { checkIsUserLogged, logoutUser, logUser } from '@/api/generated/endpoints/auth/auth'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/api/generated/endpoints/auth/auth', () => ({
  checkIsUserLogged: vi.fn(),
  logoutUser: vi.fn(),
  logUser: vi.fn(),
}))

function httpError(status: number): AxiosError {
  return new AxiosError('Request failed', undefined, undefined, undefined, {
    status,
    statusText: '',
    data: null,
    headers: {},
    config: { headers: new AxiosHeaders() },
  })
}

describe('auth store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('checkIsLogged marks the user as logged out on 401', async () => {
    vi.mocked(checkIsUserLogged).mockRejectedValueOnce(httpError(401))
    const store = useAuthStore()

    await store.checkIsLogged()

    expect(store.isUserLogged).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('checkIsLogged rethrows errors other than 401', async () => {
    const error = httpError(500)
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

  it('logout resets the session even when the request fails', async () => {
    vi.mocked(checkIsUserLogged).mockResolvedValueOnce({ isAdmin: true })
    vi.mocked(logoutUser).mockRejectedValueOnce(httpError(500))
    const store = useAuthStore()
    await store.login('user', 'password')

    await expect(store.logout()).rejects.toBeInstanceOf(AxiosError)

    expect(store.isUserLogged).toBe(false)
    expect(store.isAdmin).toBe(false)
  })
})
