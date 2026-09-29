import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  addPublicRegulation,
  confirmPublicRegulationUpload,
} from '@/api/generated/endpoints/regulations/regulations'
import {
  addUserRegulation,
  confirmUserRegulationUpload,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import { uploadFileToStorage } from '@/utils/storage'
import { useRegulationUpload } from '@/composables/useRegulationUpload'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  addPublicRegulation: vi.fn(),
  confirmPublicRegulationUpload: vi.fn(),
}))

vi.mock('@/api/generated/endpoints/user-regulations/user-regulations', () => ({
  addUserRegulation: vi.fn(),
  confirmUserRegulationUpload: vi.fn(),
}))

vi.mock('@/utils/storage', () => ({
  uploadFileToStorage: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}))

function prepareUpload(target: 'user' | 'public', presentationName: string) {
  const upload = useRegulationUpload()
  upload.setFile(new File(['dummy'], 'doc.pdf', { type: 'application/pdf' }))
  upload.presentationName.value = presentationName
  upload.target.value = target
  return upload
}

describe('useRegulationUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('submit orchestrates user flow: create -> upload -> confirm', async () => {
    const uploadTarget = { id: 'uuid-user-1', url: 'https://s3.local/upload', fields: {} }
    vi.mocked(addUserRegulation).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload('user', 'User Doc')
    upload.selectedRegulationType.value = 'STATUTE'
    const result = await upload.submit()

    expect(addUserRegulation).toHaveBeenCalledWith({ name: 'User Doc', regulationType: 'STATUTE' })
    expect(uploadFileToStorage).toHaveBeenCalledWith(uploadTarget, expect.any(File))
    expect(confirmUserRegulationUpload).toHaveBeenCalledWith('uuid-user-1')
    expect(result?.regulation).toEqual({
      id: 'uuid-user-1',
      createDate: expect.any(String),
      presentationName: 'User Doc',
      description: null,
      regulationType: 'STATUTE',
      preparationStatus: 'IN_PROGRESS',
    })
  })

  it('submit orchestrates public flow: create -> upload -> confirm', async () => {
    const uploadTarget = { id: 'uuid-pub-1', url: 'https://s3.local/upload', fields: {} }
    vi.mocked(addPublicRegulation).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload('public', 'Public Doc')
    upload.selectedRegulationType.value = 'ACT'
    const result = await upload.submit()

    expect(addPublicRegulation).toHaveBeenCalledWith({ name: 'Public Doc', regulationType: 'ACT' })
    expect(uploadFileToStorage).toHaveBeenCalledWith(uploadTarget, expect.any(File))
    expect(confirmPublicRegulationUpload).toHaveBeenCalledWith('uuid-pub-1')
    expect(result?.regulation.preparationStatus).toBe('IN_PROGRESS')
  })

  it('submit keeps the uploaded regulation when confirm-upload fails', async () => {
    vi.mocked(addUserRegulation).mockResolvedValueOnce({
      id: 'uuid-user-2',
      url: 'https://s3.local/upload',
      fields: {},
    })
    vi.mocked(confirmUserRegulationUpload).mockRejectedValueOnce(
      new Error('Preparation service not working!'),
    )

    const upload = prepareUpload('user', 'User Doc')
    const result = await upload.submit()

    expect(result?.regulation).toEqual({
      id: 'uuid-user-2',
      createDate: expect.any(String),
      presentationName: 'User Doc',
      description: null,
      regulationType: null,
      preparationStatus: 'NOT_STARTED',
    })
  })
})
