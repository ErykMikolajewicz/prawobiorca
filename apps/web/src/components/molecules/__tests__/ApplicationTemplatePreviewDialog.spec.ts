import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import axios from 'axios'
import ElementPlus from 'element-plus'
import { renderAsync } from 'docx-preview'
import ApplicationTemplatePreviewDialog from '../ApplicationTemplatePreviewDialog.vue'
import { page, shownMessages } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import { getAdminApplicationTemplateDownloadUrl } from '@/api/generated/endpoints/application-templates/application-templates'

vi.mock('@/api/generated/endpoints/application-templates/application-templates')
vi.mock('docx-preview', () => ({ renderAsync: vi.fn() }))

const templateFile = new Blob(['docx'])

function mountDialog(): VueWrapper {
  return mount(ApplicationTemplatePreviewDialog, {
    props: { modelValue: false, templateId: 'template-1' },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

async function open(wrapper: VueWrapper) {
  await wrapper.setProps({ modelValue: true })
  await flushPromises()
}

describe('ApplicationTemplatePreviewDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(axios, 'get').mockResolvedValue({ data: templateFile })
    vi.mocked(getAdminApplicationTemplateDownloadUrl).mockResolvedValue(
      'https://storage.example.com/template.docx',
    )
    vi.mocked(renderAsync).mockImplementation((_file, container) => {
      container.append('Treść szablonu')
      return Promise.resolve()
    })
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('does not load the template file until it is opened', async () => {
    mountDialog()
    await flushPromises()

    expect(getAdminApplicationTemplateDownloadUrl).not.toHaveBeenCalled()
  })

  it('renders the file of the template when opened', async () => {
    const wrapper = mountDialog()

    await open(wrapper)

    expect(getAdminApplicationTemplateDownloadUrl).toHaveBeenCalledExactlyOnceWith('template-1')
    expect(axios.get).toHaveBeenCalledExactlyOnceWith('https://storage.example.com/template.docx', {
      responseType: 'blob',
    })
    expect(vi.mocked(renderAsync).mock.calls[0]?.[0]).toBe(templateFile)
    expect(document.querySelector('.preview-container')?.textContent).toBe('Treść szablonu')
  })

  it.each(['success', 'failure'])('removes the loading indicator after %s', async (outcome) => {
    let finishDownload: ((url: string) => void) | undefined
    let failDownload: ((reason: unknown) => void) | undefined
    const download = new Promise<string>((resolve, reject) => {
      finishDownload = resolve
      failDownload = reject
    })
    vi.mocked(getAdminApplicationTemplateDownloadUrl).mockReturnValueOnce(download)
    const wrapper = mountDialog()

    await open(wrapper)

    expect(page().find('.preview-container .el-loading-mask').isVisible()).toBe(true)

    if (outcome === 'success') {
      finishDownload?.('https://storage.example.com/template.docx')
    } else {
      failDownload?.(createHttpError(404))
    }
    await flushPromises()

    await vi.waitFor(() => {
      expect(page().find('.preview-container .el-loading-mask').exists()).toBe(false)
    })
  })

  it('downloads the file through the dev storage proxy', async () => {
    vi.stubEnv('VITE_DEV_STORAGE_ORIGIN', 'http://localhost:9000')
    vi.mocked(getAdminApplicationTemplateDownloadUrl).mockResolvedValue(
      'http://localhost:9000/templates/template.docx',
    )
    const wrapper = mountDialog()

    await open(wrapper)

    expect(axios.get).toHaveBeenCalledExactlyOnceWith('/storage/templates/template.docx', {
      responseType: 'blob',
    })
  })

  it('renders the template chosen before the dialog was opened again', async () => {
    const wrapper = mountDialog()
    await open(wrapper)
    await wrapper.setProps({ modelValue: false })

    await wrapper.setProps({ templateId: 'template-2' })
    await open(wrapper)

    expect(getAdminApplicationTemplateDownloadUrl).toHaveBeenLastCalledWith('template-2')
  })

  it('removes the rendered file after the dialog is closed', async () => {
    const wrapper = mountDialog()
    await open(wrapper)

    wrapper.findComponent({ name: 'ElDialog' }).vm.$emit('closed')

    expect(document.querySelector('.preview-container')?.textContent).toBe('')
  })

  it('reports a file that could not be loaded', async () => {
    vi.mocked(getAdminApplicationTemplateDownloadUrl).mockRejectedValue(createHttpError(404))
    const wrapper = mountDialog()

    await open(wrapper)

    expect(shownMessages('error')).toEqual(['Nie udało się wczytać podglądu szablonu.'])
    expect(renderAsync).not.toHaveBeenCalled()
  })
})
