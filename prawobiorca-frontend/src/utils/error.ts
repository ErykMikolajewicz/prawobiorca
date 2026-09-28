import axios from 'axios'
import { ElMessage } from 'element-plus'

import { SessionExpiredError } from '@/api/sessionExpiry'

export type ApiErrorMessageOptions = {
  conflictMessage?: string
  defaultServerMessage?: string
  serviceUnavailableMessage?: string
  unauthorizedMessage?: string
}

export function getApiErrorMessage(error: unknown, options?: ApiErrorMessageOptions): string {
  const defaultServer =
    options?.defaultServerMessage ?? 'Wystąpił błąd po stronie serwera. Spróbuj ponownie później.'
  const conflictMsg = options?.conflictMessage ?? 'Zasób jest już zajęty.'
  const serviceUnavailableMsg =
    options?.serviceUnavailableMessage ??
    'Serwis jest chwilowo niedostępny. Spróbuj ponownie później.'
  const unauthorizedMsg = options?.unauthorizedMessage ?? 'Sesja wygasła. Zaloguj się ponownie.'

  if (!axios.isAxiosError(error)) {
    return 'Wystąpił błąd. Spróbuj ponownie.'
  }

  if (error.response) {
    const status = error.response.status
    if (status === 401) return unauthorizedMsg
    if (status === 409) return conflictMsg
    if (status === 503) return serviceUnavailableMsg

    return defaultServer
  }

  if (error.request) {
    return 'Nie można połączyć się z serwerem. Sprawdź połączenie sieciowe.'
  }

  return 'Wystąpił błąd. Spróbuj ponownie.'
}

export function showApiError(error: unknown, options?: ApiErrorMessageOptions): void {
  if (error instanceof SessionExpiredError) return

  ElMessage.error(getApiErrorMessage(error, options))
  console.error(error)
}
