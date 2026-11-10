import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ElMessage } from 'element-plus'
import { createHttpError, createNetworkError } from '@/__tests__/factories'
import { SessionExpiredError } from '@/api/sessionExpiry'
import { getApiErrorMessage, showApiError } from '@/utils/error'

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

describe('error utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('showApiError shows message for regular errors', () => {
    showApiError(new Error('boom'))

    expect(ElMessage.error).toHaveBeenCalledExactlyOnceWith('Wystąpił błąd. Spróbuj ponownie.')
  })

  it('showApiError shows the message matching the response status', () => {
    showApiError(createHttpError(409), { conflictMessage: 'Nazwa jest już zajęta.' })

    expect(ElMessage.error).toHaveBeenCalledExactlyOnceWith('Nazwa jest już zajęta.')
  })

  it('showApiError skips SessionExpiredError', () => {
    showApiError(new SessionExpiredError('Session expired'))

    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it.each([404, 422])('getApiErrorMessage does not blame the server for %i', (status) => {
    expect(getApiErrorMessage(createHttpError(status))).toBe(
      'Nie udało się wykonać operacji. Sprawdź dane i spróbuj ponownie.',
    )
  })

  it('getApiErrorMessage reports a server error for 500', () => {
    expect(getApiErrorMessage(createHttpError(500))).toBe(
      'Wystąpił błąd po stronie serwera. Spróbuj ponownie później.',
    )
  })

  it.each([
    [401, 'Sesja wygasła. Zaloguj się ponownie.'],
    [409, 'Zasób jest już zajęty.'],
    [503, 'Serwis jest chwilowo niedostępny. Spróbuj ponownie później.'],
  ])('getApiErrorMessage explains %i even when defaultMessage is given', (status, message) => {
    expect(getApiErrorMessage(createHttpError(status), { defaultMessage: 'Nie udało się.' })).toBe(
      message,
    )
  })

  it.each([
    [401, { unauthorizedMessage: 'Błędne hasło.' }, 'Błędne hasło.'],
    [409, { conflictMessage: 'Nazwa zajęta.' }, 'Nazwa zajęta.'],
    [503, { serviceUnavailableMessage: 'Trwa przerwa.' }, 'Trwa przerwa.'],
  ])('getApiErrorMessage uses the custom message for %i', (status, options, message) => {
    expect(getApiErrorMessage(createHttpError(status), options)).toBe(message)
  })

  it('getApiErrorMessage reports a connection problem when there is no response', () => {
    expect(getApiErrorMessage(createNetworkError(), { defaultMessage: 'Nie udało się.' })).toBe(
      'Nie można połączyć się z serwerem. Sprawdź połączenie sieciowe.',
    )
  })

  it('getApiErrorMessage does not use defaultMessage for errors not coming from the API', () => {
    expect(getApiErrorMessage(new Error('boom'), { defaultMessage: 'Nie udało się.' })).toBe(
      'Wystąpił błąd. Spróbuj ponownie.',
    )
  })

  it.each([404, 500])('getApiErrorMessage prefers defaultMessage for %i', (status) => {
    expect(getApiErrorMessage(createHttpError(status), { defaultMessage: 'Nie udało się.' })).toBe(
      'Nie udało się.',
    )
  })
})
