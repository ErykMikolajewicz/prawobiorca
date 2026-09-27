import axios, { AxiosError } from 'axios'

export function getApiErrorMessage(
  error: unknown,
  options?: {
    conflictMessage?: string
    defaultServerMessage?: string
    serviceUnavailableMessage?: string
    unauthorizedMessage?: string
  },
): string {
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

  const axiosErr = error as AxiosError

  if (axiosErr.response) {
    const status = axiosErr.response.status
    if (status === 401) return unauthorizedMsg
    if (status === 409) return conflictMsg
    if (status === 503) return serviceUnavailableMsg

    return defaultServer
  }

  if (axiosErr.request) {
    return 'Nie można połączyć się z serwerem. Sprawdź połączenie sieciowe.'
  }

  return 'Wystąpił błąd. Spróbuj ponownie.'
}
