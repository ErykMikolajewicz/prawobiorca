import { describe, it, expect, vi, beforeEach } from 'vitest'
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

  it('submit orchestrates flow: create -> upload -> confirm', async () => {
    vi.mocked(addApplicationTemplate).mockResolvedValueOnce(uploadTarget)

    const upload = prepareUpload()
    const templateId = await upload.submit()

    expect(addApplicationTemplate).toHaveBeenCalledWith({ name: 'Wniosek o urlop' })
    expect(uploadFileToStorage).toHaveBeenCalledWith(uploadTarget, expect.any(File))
    expect(confirmApplicationTemplateUpload).toHaveBeenCalledWith('template-1')
    expect(templateId).toBe('template-1')
    expect(ElMessage.success).toHaveBeenCalled()
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
    expect(ElMessage.warning).toHaveBeenCalledTimes(2)
    expect(addApplicationTemplate).not.toHaveBeenCalled()
  })
})
