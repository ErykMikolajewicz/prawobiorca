import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { getPublicRegulationDownloadUrl as fetchPublicRegulationDownloadUrl } from '@/api/generated/endpoints/regulations/regulations'
import { getUserRegulationDownloadUrl as fetchUserRegulationDownloadUrl } from '@/api/generated/endpoints/user-regulations/user-regulations'
import {
  getPublicRegulationDownloadUrl,
  getUserRegulationDownloadUrl,
  uploadFileToStorage,
} from '@/utils/storage'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  getPublicRegulationDownloadUrl: vi.fn(),
}))

vi.mock('@/api/generated/endpoints/user-regulations/user-regulations', () => ({
  getUserRegulationDownloadUrl: vi.fn(),
}))

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}))

describe('storage utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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

  it('uploadFileToStorage rewrites localhost:9000 to /storage in dev environment', async () => {
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

  it('getUserRegulationDownloadUrl retrieves download url and rewrites localhost:9000 in dev', async () => {
    vi.mocked(fetchUserRegulationDownloadUrl).mockResolvedValueOnce(
      'http://localhost:9000/regulations/uuid-123.pdf',
    )
    const url = await getUserRegulationDownloadUrl('uuid-123')
    expect(fetchUserRegulationDownloadUrl).toHaveBeenCalledWith('uuid-123')
    expect(url).toBe('/storage/regulations/uuid-123.pdf')
  })

  it('getPublicRegulationDownloadUrl retrieves download url and rewrites localhost:9000 in dev', async () => {
    vi.mocked(fetchPublicRegulationDownloadUrl).mockResolvedValueOnce(
      'http://localhost:9000/regulations/uuid-456.pdf',
    )
    const url = await getPublicRegulationDownloadUrl('uuid-456')
    expect(fetchPublicRegulationDownloadUrl).toHaveBeenCalledWith('uuid-456')
    expect(url).toBe('/storage/regulations/uuid-456.pdf')
  })
})
