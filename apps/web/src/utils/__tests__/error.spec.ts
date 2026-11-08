import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { ElMessage } from 'element-plus'
import { SessionExpiredError } from '@/api/sessionExpiry'
import { getApiErrorMessage, showApiError } from '@/utils/error'

function httpError(status: number): AxiosError {
  return new AxiosError('Request failed', undefined, undefined, undefined, {
    status,
    statusText: '',
    data: null,
    headers: {},
    config: { headers: new AxiosHeaders() },
  })
}

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

    expect(ElMessage.error).toHaveBeenCalledOnce()
  })

  it('showApiError skips SessionExpiredError', () => {
    showApiError(new SessionExpiredError('Session expired'))

    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it.each([404, 422])('getApiErrorMessage does not blame the server for %i', (status) => {
    expect(getApiErrorMessage(httpError(status))).toBe(
      'Nie udało się wykonać operacji. Sprawdź dane i spróbuj ponownie.',
    )
  })

  it('getApiErrorMessage reports a server error for 500', () => {
    expect(getApiErrorMessage(httpError(500))).toBe(
      'Wystąpił błąd po stronie serwera. Spróbuj ponownie później.',
    )
  })

  it.each([404, 500])('getApiErrorMessage prefers defaultMessage for %i', (status) => {
    expect(getApiErrorMessage(httpError(status), { defaultMessage: 'Nie udało się.' })).toBe(
      'Nie udało się.',
    )
  })
})
