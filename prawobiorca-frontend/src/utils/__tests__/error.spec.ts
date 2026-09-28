import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ElMessage } from 'element-plus'
import { SessionExpiredError } from '@/api/sessionExpiry'
import { showApiError } from '@/utils/error'

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
})
