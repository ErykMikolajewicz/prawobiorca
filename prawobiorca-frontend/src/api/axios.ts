import axios, { type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'

import { notifySessionExpired, SessionExpiredError } from '@/api/sessionExpiry'

export const prawobiorcaClient = axios.create()
prawobiorcaClient.defaults.withCredentials = true

export async function prawobiorcaRequest<T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig,
): Promise<T> {
  const response = await prawobiorcaClient<T>({ ...config, ...options })
  return response.data
}

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

/**
 * Ścieżki, dla których 401 nie oznacza wygasłego access tokena:
 * `/auth/me` to sonda stanu sesji (401 = niezalogowany), a pozostałe same obsługują tokeny.
 */
const NOT_REFRESHABLE_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout', '/auth/me']

function isRefreshable(url: string | undefined): boolean {
  if (!url) return false
  const path = url.split('?')[0] ?? url
  return !NOT_REFRESHABLE_PATHS.some((excluded) => path.endsWith(excluded))
}

let refreshPromise: Promise<void> | null = null

/**
 * Odświeża tokeny na podstawie ciasteczka refresh. Równoległe wywołania współdzielą
 * jedno żądanie, więc kilka jednoczesnych 401 nie wywoła kilku odświeżeń.
 */
function refreshTokens(): Promise<void> {
  refreshPromise ??= prawobiorcaClient
    .post('/api/auth/refresh')
    .then(() => undefined)
    .finally(() => {
      refreshPromise = null
    })
  return refreshPromise
}

prawobiorcaClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) {
      return Promise.reject(error)
    }

    const config = error.config as RetriableConfig | undefined
    if (!config || config._retried || !isRefreshable(config.url)) {
      return Promise.reject(error)
    }

    config._retried = true

    try {
      await refreshTokens()
    } catch (refreshError: unknown) {
      if (!axios.isAxiosError(refreshError) || refreshError.response?.status !== 401) {
        return Promise.reject(refreshError)
      }
      notifySessionExpired()
      return Promise.reject(new SessionExpiredError('Session expired'))
    }

    return prawobiorcaClient(config)
  },
)
