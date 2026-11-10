import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  addApplicationTemplate,
  confirmApplicationTemplateUpload,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { uploadFileToStorage } from '@/utils/storage'
import { showApiError } from '@/utils/error'
import { useApplicationTemplateUpload } from '@/composables/useApplicationTemplateUpload'

vi.mock('@/api/generated/endpoints/application-templates/application-templates', () => ({
  addApplicationTemplate: vi.fn(),
  confirmApplicationTemplateUpload: vi.fn(),
}))

vi.mock('@/utils/storage', () => ({
  uploadFileToStorage: vi.fn(),
}))

vi.mock('@/utils/error', () => ({
  showApiError: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}))

const uploadTarget = { id: 'template-1', url: 'https://s3.local/upload', fields: {} }

function prepareUpload() {
  const upload = useApplicationTemplateUpload()
  upload.setFile(new File(['dummy'], 'Wniosek o urlop.docx'))
  return upload
}

describe('useApplicationTemplateUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('setFile uses file name without extension as template name', () => {
    const upload = prepareUpload()

    expect(upload.name.value).toBe('Wniosek o urlop')
  })

  it('setFile keeps the name when the file is cleared', () => {
    const upload = prepareUpload()

    upload.setFile(null)

    expect(upload.selectedFile.value).toBeNull()
    expect(upload.name.value).toBe('Wniosek o urlop')
  })

  it('resetForm clears the file and the name', () => {
    const upload = prepareUpload()

    upload.resetForm()

    expect(upload.selectedFile.value).toBeNull()
    expect(upload.name.value).toBe('')
  })

  it('submit trims the template name', async () => {
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload()
    upload.name.value = '  Wniosek o urlop  '
    await upload.submit()

    expect(addApplicationTemplate).toHaveBeenCalledWith(
      { name: 'Wniosek o urlop' },
      { signal: expect.any(AbortSignal) },
    )
  })

  it('submit marks the form as submitting until the upload ends', async () => {
    let finishUpload: (() => void) | undefined
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)
    vi.mocked(uploadFileToStorage).mockImplementationOnce(
      () => new Promise((resolve) => (finishUpload = resolve)),
    )

    const upload = prepareUpload()
    expect(upload.isSubmitting.value).toBe(false)

    const submission = upload.submit()
    await vi.waitFor(() => expect(uploadFileToStorage).toHaveBeenCalled())
    expect(upload.isSubmitting.value).toBe(true)

    finishUpload?.()
    await submission
    expect(upload.isSubmitting.value).toBe(false)
  })

  it('submit orchestrates flow: create -> upload -> confirm', async () => {
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload()
    const templateId = await upload.submit()

    const signal = expect.any(AbortSignal)
    expect(addApplicationTemplate).toHaveBeenCalledWith({ name: 'Wniosek o urlop' }, { signal })
    expect(uploadFileToStorage).toHaveBeenCalledWith(uploadTarget, expect.any(File), signal)
    expect(confirmApplicationTemplateUpload).toHaveBeenCalledWith('template-1', { signal })
    expect(templateId).toBe('template-1')
    expect(ElMessage.success).toHaveBeenCalledExactlyOnceWith(
      'Szablon został dodany. Skonfiguruj pola i instrukcje dla AI.',
    )
  })

  it('submit returns null and shows upload error when sending file fails', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)
    vi.mocked(uploadFileToStorage).mockRejectedValueOnce(new Error('timeout'))

    const upload = prepareUpload()
    const templateId = await upload.submit()

    expect(templateId).toBeNull()
    expect(ElMessage.error).toHaveBeenCalledWith(
      'Nie udało się wysłać pliku szablonu. Spróbuj ponownie.',
    )
    expect(showApiError).not.toHaveBeenCalled()
    expect(confirmApplicationTemplateUpload).not.toHaveBeenCalled()
    expect(upload.isSubmitting.value).toBe(false)
  })

  it('cancelSubmit aborts sending file without showing an error', async () => {
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)
    vi.mocked(uploadFileToStorage).mockImplementationOnce(
      (_target, _file, signal) =>
        new Promise((_resolve, reject) => {
          signal?.addEventListener('abort', () => reject(new axios.CanceledError()))
        }),
    )

    const upload = prepareUpload()
    const submission = upload.submit()
    await vi.waitFor(() => expect(uploadFileToStorage).toHaveBeenCalled())
    upload.cancelSubmit()

    expect(await submission).toBeNull()
    expect(ElMessage.error).not.toHaveBeenCalled()
    expect(showApiError).not.toHaveBeenCalled()
    expect(confirmApplicationTemplateUpload).not.toHaveBeenCalled()
    expect(upload.isSubmitting.value).toBe(false)
  })

  it('submit returns null without error when cancelled during confirmation', async () => {
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)
    vi.mocked(confirmApplicationTemplateUpload).mockRejectedValueOnce(new axios.CanceledError())

    const upload = prepareUpload()

    expect(await upload.submit()).toBeNull()
    expect(showApiError).not.toHaveBeenCalled()
    expect(ElMessage.success).not.toHaveBeenCalled()
  })

  it('submit returns created template id when confirmation fails', async () => {
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)
    vi.mocked(confirmApplicationTemplateUpload).mockRejectedValueOnce(new Error('Invalid template'))

    const upload = prepareUpload()
    const templateId = await upload.submit()

    expect(templateId).toBe('template-1')
    expect(showApiError).toHaveBeenCalled()
    expect(upload.isSubmitting.value).toBe(false)
  })

  it('submit returns null when template was not created', async () => {
    vi.mocked(addApplicationTemplate).mockRejectedValueOnce(new Error('Network error'))

    const upload = prepareUpload()
    const templateId = await upload.submit()

    expect(templateId).toBeNull()
    expect(uploadFileToStorage).not.toHaveBeenCalled()
    expect(showApiError).toHaveBeenCalled()
  })

  it('submit requires file and name', async () => {
    const upload = useApplicationTemplateUpload()

    expect(await upload.submit()).toBeNull()

    upload.setFile(new File(['dummy'], 'template.docx'))
    upload.name.value = ' '

    expect(await upload.submit()).toBeNull()
    expect(vi.mocked(ElMessage.warning).mock.calls).toEqual([
      ['Wybierz plik szablonu.'],
      ['Podaj nazwę szablonu.'],
    ])
    expect(addApplicationTemplate).not.toHaveBeenCalled()
  })
})
