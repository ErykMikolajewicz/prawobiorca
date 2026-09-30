import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { prawobiorcaClient } from '@/api/axios'
import {
  uploadUserRegulation,
  uploadPublicRegulation,
  retryUserRegulationPreparation,
  retryPublicRegulationPreparation,
  createUserRegulation,
  createPublicRegulation,
  uploadFileToStorage,
  confirmUserRegulationUpload,
  confirmPublicRegulationUpload,
  getUserRegulationDownloadUrl,
  getPublicRegulationDownloadUrl,
} from '@/api/regulations'

vi.mock('@/api/axios', () => ({
  prawobiorcaClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}))

describe('regulations API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('createUserRegulation posts JSON data and returns upload target', async () => {
    const mockTarget = {
      id: 'uuid-123',
      url: 'https://storage.example.com',
      fields: { key: 'val' },
    }
    vi.mocked(prawobiorcaClient.post).mockResolvedValueOnce({ data: mockTarget })
    const target = await createUserRegulation({ name: 'Regulamin', regulationType: 'STATUTE' })
    expect(prawobiorcaClient.post).toHaveBeenCalledWith('/user/regulations', {
      name: 'Regulamin',
      regulationType: 'STATUTE',
    })
    expect(target).toEqual(mockTarget)
  })

  it('createPublicRegulation posts JSON data and returns upload target', async () => {
    const mockTarget = {
      id: 'uuid-456',
      url: 'https://storage.example.com',
      fields: { key: 'val' },
    }
    vi.mocked(prawobiorcaClient.post).mockResolvedValueOnce({ data: mockTarget })
    const target = await createPublicRegulation({ name: 'Ustawa', regulationType: 'ACT' })
    expect(prawobiorcaClient.post).toHaveBeenCalledWith('/regulations', {
      name: 'Ustawa',
      regulationType: 'ACT',
    })
    expect(target).toEqual(mockTarget)
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

  it('confirmUserRegulationUpload sends POST to confirm endpoint', async () => {
    vi.mocked(prawobiorcaClient.post).mockResolvedValueOnce({ status: 204 })
    await confirmUserRegulationUpload('uuid-123')
    expect(prawobiorcaClient.post).toHaveBeenCalledWith('/user/regulations/uuid-123/confirm-upload')
  })

  it('confirmPublicRegulationUpload sends POST to confirm endpoint', async () => {
    vi.mocked(prawobiorcaClient.post).mockResolvedValueOnce({ status: 204 })
    await confirmPublicRegulationUpload('uuid-456')
    expect(prawobiorcaClient.post).toHaveBeenCalledWith('/regulations/uuid-456/confirm-upload')
  })

  it('getUserRegulationDownloadUrl retrieves download url and rewrites localhost:9000 in dev', async () => {
    vi.mocked(prawobiorcaClient.get).mockResolvedValueOnce({
      data: 'http://localhost:9000/regulations/uuid-123.pdf',
    })
    const url = await getUserRegulationDownloadUrl('uuid-123')
    expect(prawobiorcaClient.get).toHaveBeenCalledWith('/user/regulations/uuid-123/download-url')
    expect(url).toBe('/storage/regulations/uuid-123.pdf')
  })

  it('getPublicRegulationDownloadUrl retrieves download url and rewrites localhost:9000 in dev', async () => {
    vi.mocked(prawobiorcaClient.get).mockResolvedValueOnce({
      data: 'http://localhost:9000/regulations/uuid-456.pdf',
    })
    const url = await getPublicRegulationDownloadUrl('uuid-456')
    expect(prawobiorcaClient.get).toHaveBeenCalledWith('/regulations/uuid-456/download-url')
    expect(url).toBe('/storage/regulations/uuid-456.pdf')
  })

  it('uploadUserRegulation orchestrates full flow: create -> upload -> confirm', async () => {
    vi.mocked(prawobiorcaClient.post)
      .mockResolvedValueOnce({
        data: {
          id: 'uuid-user-1',
          url: 'https://s3.local/upload',
          fields: { token: 'xyz' },
        },
      })
      .mockResolvedValueOnce({ status: 204 })
    vi.mocked(axios.post).mockResolvedValueOnce({ status: 200 })

    const file = new File(['dummy'], 'user_doc.pdf', { type: 'application/pdf' })
    const result = await uploadUserRegulation(file, 'User Doc', 'STATUTE')

    expect(result).toEqual({ id: 'uuid-user-1', preparationStatus: 'IN_PROGRESS' })
    expect(prawobiorcaClient.post).toHaveBeenNthCalledWith(1, '/user/regulations', {
      name: 'User Doc',
      regulationType: 'STATUTE',
    })
    expect(axios.post).toHaveBeenCalledWith('https://s3.local/upload', expect.any(FormData))
    expect(prawobiorcaClient.post).toHaveBeenNthCalledWith(
      2,
      '/user/regulations/uuid-user-1/confirm-upload',
    )
  })

  it('uploadPublicRegulation orchestrates flow: create -> upload -> confirm', async () => {
    vi.mocked(prawobiorcaClient.post)
      .mockResolvedValueOnce({
        data: {
          id: 'uuid-pub-1',
          url: 'https://s3.local/upload',
          fields: { token: 'xyz' },
        },
      })
      .mockResolvedValueOnce({ status: 204 })
    vi.mocked(axios.post).mockResolvedValueOnce({ status: 200 })

    const file = new File(['dummy'], 'pub_doc.pdf', { type: 'application/pdf' })
    const result = await uploadPublicRegulation(file, 'Public Doc', 'ACT')

    expect(result).toEqual({ id: 'uuid-pub-1', preparationStatus: 'IN_PROGRESS' })
    expect(prawobiorcaClient.post).toHaveBeenNthCalledWith(1, '/regulations', {
      name: 'Public Doc',
      regulationType: 'ACT',
    })
    expect(axios.post).toHaveBeenCalledWith('https://s3.local/upload', expect.any(FormData))
    expect(prawobiorcaClient.post).toHaveBeenNthCalledWith(
      2,
      '/regulations/uuid-pub-1/confirm-upload',
    )
  })

  it('uploadUserRegulation keeps the uploaded regulation when confirm-upload fails', async () => {
    vi.mocked(prawobiorcaClient.post)
      .mockResolvedValueOnce({
        data: {
          id: 'uuid-user-2',
          url: 'https://s3.local/upload',
          fields: { token: 'xyz' },
        },
      })
      .mockRejectedValueOnce(new Error('Preparation service not working!'))
    vi.mocked(axios.post).mockResolvedValueOnce({ status: 200 })

    const file = new File(['dummy'], 'user_doc.pdf', { type: 'application/pdf' })
    const result = await uploadUserRegulation(file, 'User Doc')

    expect(result).toEqual({ id: 'uuid-user-2', preparationStatus: 'NOT_STARTED' })
  })

  it('retryUserRegulationPreparation sends POST to user preparation retry endpoint', async () => {
    vi.mocked(prawobiorcaClient.post).mockResolvedValueOnce({ status: 202 })
    await retryUserRegulationPreparation('uuid-123')
    expect(prawobiorcaClient.post).toHaveBeenCalledWith(
      '/user/regulations/uuid-123/preparation-retry',
    )
  })

  it('retryPublicRegulationPreparation sends POST to public preparation retry endpoint', async () => {
    vi.mocked(prawobiorcaClient.post).mockResolvedValueOnce({ status: 202 })
    await retryPublicRegulationPreparation('uuid-456')
    expect(prawobiorcaClient.post).toHaveBeenCalledWith('/regulations/uuid-456/preparation-retry')
  })
})
