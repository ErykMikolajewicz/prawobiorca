import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  AxiosError,
  AxiosHeaders,
  type AxiosAdapter,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import { prawobiorcaClient } from '@/api/axios'
import { notifySessionExpired } from '@/api/sessionExpiry'

vi.mock('@/api/sessionExpiry', () => ({
  notifySessionExpired: vi.fn(),
  setSessionExpiredHandler: vi.fn(),
}))

function response(config: InternalAxiosRequestConfig, status: number): AxiosResponse {
  return {
    data: {},
    status,
    statusText: String(status),
    headers: new AxiosHeaders(),
    config,
  }
}

function unauthorized(config: InternalAxiosRequestConfig): AxiosError {
  return new AxiosError(
    'Unauthorized',
    AxiosError.ERR_BAD_REQUEST,
    config,
    {},
    response(config, 401),
  )
}

/** Adapter zwracający statusy wg kolejki na ścieżkę; brak wpisu oznacza 200. */
function adapterFor(statuses: Record<string, number[]>): AxiosAdapter {
  return vi.fn(async (config: InternalAxiosRequestConfig) => {
    const queue = statuses[config.url ?? '']
    const status = queue?.shift() ?? 200
    if (status === 401) throw unauthorized(config)
    return response(config, status)
  })
}

function useAdapter(statuses: Record<string, number[]>) {
  const adapter = adapterFor(statuses)
  prawobiorcaClient.defaults.adapter = adapter
  return adapter as ReturnType<typeof vi.fn>
}

function calledPaths(adapter: ReturnType<typeof vi.fn>): Array<string | undefined> {
  return adapter.mock.calls.map(([config]) => (config as InternalAxiosRequestConfig).url)
}

describe('prawobiorcaClient refresh interceptor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('odświeża tokeny po 401 i ponawia oryginalne żądanie', async () => {
    const adapter = useAdapter({ '/api/user/cases': [401, 200] })

    const result = await prawobiorcaClient.get('/api/user/cases')

    expect(result.status).toBe(200)
    expect(calledPaths(adapter)).toEqual([
      '/api/user/cases',
      '/api/auth/refresh',
      '/api/user/cases',
    ])
    expect(notifySessionExpired).not.toHaveBeenCalled()
  })

  it('odświeża tokeny raz dla równoległych 401', async () => {
    const adapter = useAdapter({
      '/api/user/cases': [401, 200],
      '/api/user/regulations': [401, 200],
      '/api/user/cases/abc/documents': [401, 200],
    })

    const results = await Promise.all([
      prawobiorcaClient.get('/api/user/cases'),
      prawobiorcaClient.get('/api/user/regulations'),
      prawobiorcaClient.get('/api/user/cases/abc/documents'),
    ])

    expect(results.map((r) => r.status)).toEqual([200, 200, 200])
    expect(calledPaths(adapter).filter((url) => url === '/api/auth/refresh')).toHaveLength(1)
  })

  it('zgłasza wygaśnięcie sesji i propaguje pierwotny błąd, gdy refresh też zwróci 401', async () => {
    const adapter = useAdapter({ '/api/user/cases': [401], '/api/auth/refresh': [401] })

    await expect(prawobiorcaClient.get('/api/user/cases')).rejects.toMatchObject({
      response: { status: 401 },
      config: { url: '/api/user/cases' },
    })
    expect(notifySessionExpired).toHaveBeenCalledOnce()
    expect(calledPaths(adapter)).toEqual(['/api/user/cases', '/api/auth/refresh'])
  })

  it('nie odświeża tokenów po 401 z logowania', async () => {
    const adapter = useAdapter({ '/api/auth/login': [401] })

    await expect(prawobiorcaClient.post('/api/auth/login')).rejects.toMatchObject({
      response: { status: 401 },
    })
    expect(calledPaths(adapter)).toEqual(['/api/auth/login'])
    expect(notifySessionExpired).not.toHaveBeenCalled()
  })

  it('nie odświeża tokenów po 401 z /auth/me', async () => {
    const adapter = useAdapter({ '/api/auth/me': [401] })

    await expect(prawobiorcaClient.get('/api/auth/me')).rejects.toMatchObject({
      response: { status: 401 },
    })
    expect(calledPaths(adapter)).toEqual(['/api/auth/me'])
    expect(notifySessionExpired).not.toHaveBeenCalled()
  })

  it('nie ponawia żądania po raz drugi, gdy po odświeżeniu nadal jest 401', async () => {
    const adapter = useAdapter({ '/api/user/cases': [401, 401] })

    await expect(prawobiorcaClient.get('/api/user/cases')).rejects.toMatchObject({
      response: { status: 401 },
    })
    expect(calledPaths(adapter)).toEqual([
      '/api/user/cases',
      '/api/auth/refresh',
      '/api/user/cases',
    ])
    expect(notifySessionExpired).not.toHaveBeenCalled()
  })
})
