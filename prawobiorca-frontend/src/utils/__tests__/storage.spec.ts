import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { uploadFileToStorage } from '@/utils/storage'

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}))

describe('storage utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('uploadFileToStorage posts FormData to target url', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({ status: 204 })
    const target = {
      id: 'uuid-123',
      url: 'https://storage.example.com/upload',
      fields: { 'X-Amz-Signature': 'sig', key: 'reg.pdf' },
    }
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    await uploadFileToStorage(target, file)

    expect(axios.post).toHaveBeenCalledTimes(1)
    const [url, formData] = vi.mocked(axios.post).mock.calls[0] ?? []
    expect(url).toBe('https://storage.example.com/upload')
    expect(formData).toBeInstanceOf(FormData)
    expect((formData as FormData).get('key')).toBe('reg.pdf')
    expect((formData as FormData).get('X-Amz-Signature')).toBe('sig')
    expect((formData as FormData).get('file')).toEqual(file)
  })

  it('uploadFileToStorage rewrites the dev storage origin to /storage', async () => {
    vi.stubEnv('VITE_DEV_STORAGE_ORIGIN', 'http://localhost:9000')
    vi.mocked(axios.post).mockResolvedValueOnce({ status: 204 })
    const target = {
      id: 'uuid-123',
      url: 'http://localhost:9000/regulations',
      fields: { 'X-Amz-Signature': 'sig', key: 'reg.pdf' },
    }
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    await uploadFileToStorage(target, file)

    expect(axios.post).toHaveBeenCalledTimes(1)
    const [url] = vi.mocked(axios.post).mock.calls[0] ?? []
    expect(url).toBe('/storage/regulations')
  })

  it('uploadFileToStorage keeps the url when dev storage origin is not set', async () => {
    vi.stubEnv('VITE_DEV_STORAGE_ORIGIN', '')
    vi.mocked(axios.post).mockResolvedValueOnce({ status: 204 })
    const target = {
      id: 'uuid-123',
      url: 'http://localhost:9000/regulations',
      fields: {},
    }
    await uploadFileToStorage(target, new File(['content'], 'test.pdf'))

    const [url] = vi.mocked(axios.post).mock.calls[0] ?? []
    expect(url).toBe('http://localhost:9000/regulations')
  })
})
