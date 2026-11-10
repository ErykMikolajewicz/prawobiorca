import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ElMessage } from 'element-plus'
import { createHttpError } from '@/__tests__/factories'
import {
  addRegulation,
  confirmRegulationUpload,
} from '@/api/generated/endpoints/regulations/regulations'
import { uploadFileToStorage } from '@/utils/storage'
import { useRegulationUpload } from '@/composables/useRegulationUpload'
import type { RegulationScope } from '@/domain/regulations'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  addRegulation: vi.fn(),
  confirmRegulationUpload: vi.fn(),
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

function prepareUpload(target: RegulationScope, presentationName: string) {
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
    vi.mocked(addRegulation).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload('PRIVATE', 'User Doc')
    upload.selectedRegulationType.value = 'STATUTE'
    const result = await upload.submit()

    expect(addRegulation).toHaveBeenCalledWith({
      scope: 'PRIVATE',
      name: 'User Doc',
      regulationType: 'STATUTE',
      organizationId: null,
      suborganizationId: null,
      generateDescription: false,
    })
    expect(uploadFileToStorage).toHaveBeenCalledWith(uploadTarget, expect.any(File))
    expect(confirmRegulationUpload).toHaveBeenCalledWith('uuid-user-1')
    expect(result?.regulation).toEqual({
      id: 'uuid-user-1',
      createDate: expect.any(String),
      presentationName: 'User Doc',
      description: null,
      regulationType: 'STATUTE',
      preparationStatus: 'IN_PROGRESS',
      descriptionStatus: 'NOT_REQUESTED',
      organizationId: null,
      suborganizationId: null,
    })
  })

  it('submit orchestrates public flow: create -> upload -> confirm', async () => {
    const uploadTarget = { id: 'uuid-pub-1', url: 'https://s3.local/upload', fields: {} }
    vi.mocked(addRegulation).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload('PUBLIC', 'Public Doc')
    upload.selectedRegulationType.value = 'ACT'
    const result = await upload.submit()

    expect(addRegulation).toHaveBeenCalledWith({
      scope: 'PUBLIC',
      name: 'Public Doc',
      regulationType: 'ACT',
      organizationId: null,
      suborganizationId: null,
      generateDescription: false,
    })
    expect(uploadFileToStorage).toHaveBeenCalledWith(uploadTarget, expect.any(File))
    expect(confirmRegulationUpload).toHaveBeenCalledWith('uuid-pub-1')
    expect(result?.regulation.preparationStatus).toBe('IN_PROGRESS')
  })

  it('submit sends the selected organization for a public regulation', async () => {
    vi.mocked(addRegulation).mockResolvedValueOnce({
      id: 'uuid-pub-2',
      url: 'https://s3.local/upload',
      fields: {},
    })

    const upload = prepareUpload('PUBLIC', 'Faculty Doc')
    upload.selectedOrganizationId.value = 'pwr'
    upload.selectedSuborganizationId.value = 'w10'
    const result = await upload.submit()

    expect(addRegulation).toHaveBeenCalledWith({
      scope: 'PUBLIC',
      name: 'Faculty Doc',
      regulationType: null,
      organizationId: 'pwr',
      suborganizationId: 'w10',
      generateDescription: false,
    })
    expect(result?.regulation.organizationId).toBe('pwr')
    expect(result?.regulation.suborganizationId).toBe('w10')
  })

  it('submit requests description generation', async () => {
    vi.mocked(addRegulation).mockResolvedValueOnce({
      id: 'uuid-pub-2',
      url: 'https://s3.local/upload',
      fields: {},
    })

    const upload = prepareUpload('PUBLIC', 'Public Doc')
    upload.generateDescription.value = true
    const result = await upload.submit()

    expect(addRegulation).toHaveBeenCalledWith(
      expect.objectContaining({ generateDescription: true }),
    )
    expect(result?.regulation.descriptionStatus).toBe('IN_PROGRESS')
  })

  it('resetForm restores the initial form', () => {
    const upload = prepareUpload('PUBLIC', 'Public Doc')
    upload.selectedRegulationType.value = 'ACT'
    upload.selectedOrganizationId.value = 'pwr'
    upload.selectedSuborganizationId.value = 'w10'
    upload.generateDescription.value = true

    upload.resetForm()

    expect(upload.selectedFile.value).toBeNull()
    expect(upload.presentationName.value).toBe('')
    expect(upload.selectedRegulationType.value).toBe('')
    expect(upload.target.value).toBe('PRIVATE')
    expect(upload.selectedOrganizationId.value).toBe('')
    expect(upload.selectedSuborganizationId.value).toBe('')
    expect(upload.generateDescription.value).toBe(false)
  })

  it('setFile proposes the file name as the regulation name', () => {
    const upload = useRegulationUpload()

    upload.setFile(new File(['dummy'], 'regulamin.pdf'))

    expect(upload.presentationName.value).toBe('regulamin.pdf')
  })

  it('setFile keeps the entered name when the file is cleared', () => {
    const upload = prepareUpload('PRIVATE', 'User Doc')

    upload.setFile(null)

    expect(upload.selectedFile.value).toBeNull()
    expect(upload.presentationName.value).toBe('User Doc')
  })

  it('submit requires a file', async () => {
    const upload = useRegulationUpload()
    upload.presentationName.value = 'User Doc'

    expect(await upload.submit()).toBeNull()

    expect(ElMessage.warning).toHaveBeenCalledExactlyOnceWith('Wybierz plik do przesłania.')
    expect(addRegulation).not.toHaveBeenCalled()
  })

  it('submit requires a name', async () => {
    const upload = prepareUpload('PRIVATE', '   ')

    expect(await upload.submit()).toBeNull()

    expect(ElMessage.warning).toHaveBeenCalledExactlyOnceWith('Podaj nazwę pliku.')
    expect(addRegulation).not.toHaveBeenCalled()
  })

  it('submit trims the name', async () => {
    vi.mocked(addRegulation).mockResolvedValueOnce({ id: 'uuid-1', url: '', fields: {} })

    const upload = prepareUpload('PRIVATE', '  User Doc ')
    const result = await upload.submit()

    expect(addRegulation).toHaveBeenCalledWith(expect.objectContaining({ name: 'User Doc' }))
    expect(result?.regulation.presentationName).toBe('User Doc')
  })

  it('submit does not assign a private regulation to an organization', async () => {
    vi.mocked(addRegulation).mockResolvedValueOnce({ id: 'uuid-1', url: '', fields: {} })

    const upload = prepareUpload('PRIVATE', 'User Doc')
    upload.selectedOrganizationId.value = 'pwr'
    upload.selectedSuborganizationId.value = 'w10'
    const result = await upload.submit()

    expect(addRegulation).toHaveBeenCalledWith(
      expect.objectContaining({ organizationId: null, suborganizationId: null }),
    )
    expect(result).toMatchObject({
      target: 'PRIVATE',
      regulation: { organizationId: null, suborganizationId: null },
    })
  })

  it('submit informs that the file is being processed', async () => {
    vi.mocked(addRegulation).mockResolvedValueOnce({ id: 'uuid-1', url: '', fields: {} })

    await prepareUpload('PRIVATE', 'User Doc').submit()

    expect(ElMessage.success).toHaveBeenCalledExactlyOnceWith(
      'Plik został dodany i jest przetwarzany.',
    )
    expect(ElMessage.warning).not.toHaveBeenCalled()
  })

  it('submit marks the form as submitting until the upload ends', async () => {
    let finishUpload: (() => void) | undefined
    vi.mocked(addRegulation).mockResolvedValueOnce({ id: 'uuid-1', url: '', fields: {} })
    vi.mocked(uploadFileToStorage).mockImplementationOnce(
      () => new Promise((resolve) => (finishUpload = resolve)),
    )

    const upload = prepareUpload('PRIVATE', 'User Doc')
    expect(upload.isSubmitting.value).toBe(false)

    const submission = upload.submit()
    await vi.waitFor(() => expect(uploadFileToStorage).toHaveBeenCalled())
    expect(upload.isSubmitting.value).toBe(true)

    finishUpload?.()
    await submission
    expect(upload.isSubmitting.value).toBe(false)
  })

  it('submit shows an error and creates nothing when the regulation is rejected', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    vi.mocked(addRegulation).mockRejectedValueOnce(createHttpError(422))

    const upload = prepareUpload('PRIVATE', 'User Doc')

    expect(await upload.submit()).toBeNull()
    expect(ElMessage.error).toHaveBeenCalledExactlyOnceWith(
      'Wystąpił błąd podczas dodawania pliku.',
    )
    expect(uploadFileToStorage).not.toHaveBeenCalled()
    expect(upload.isSubmitting.value).toBe(false)
  })

  it('submit does not confirm the upload when sending the file fails', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    vi.mocked(addRegulation).mockResolvedValueOnce({ id: 'uuid-1', url: '', fields: {} })
    vi.mocked(uploadFileToStorage).mockRejectedValueOnce(new Error('timeout'))

    const upload = prepareUpload('PRIVATE', 'User Doc')

    expect(await upload.submit()).toBeNull()
    expect(confirmRegulationUpload).not.toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledOnce()
    expect(ElMessage.success).not.toHaveBeenCalled()
  })

  it('submit keeps the uploaded regulation when confirm-upload fails', async () => {
    vi.mocked(addRegulation).mockResolvedValueOnce({
      id: 'uuid-user-2',
      url: 'https://s3.local/upload',
      fields: {},
    })
    vi.mocked(confirmRegulationUpload).mockRejectedValueOnce(
      new Error('Preparation service not working!'),
    )

    vi.spyOn(console, 'error').mockImplementationOnce(() => {})

    const upload = prepareUpload('PRIVATE', 'User Doc')
    const result = await upload.submit()

    expect(ElMessage.warning).toHaveBeenCalledExactlyOnceWith(
      'Plik został wgrany, ale nie udało się rozpocząć przetwarzania.',
    )
    expect(ElMessage.success).not.toHaveBeenCalled()
    expect(result?.regulation).toEqual({
      id: 'uuid-user-2',
      createDate: expect.any(String),
      presentationName: 'User Doc',
      description: null,
      regulationType: null,
      preparationStatus: 'NOT_STARTED',
      descriptionStatus: 'NOT_REQUESTED',
      organizationId: null,
      suborganizationId: null,
    })
  })
})
