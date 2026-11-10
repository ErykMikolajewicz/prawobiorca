import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ApplicationTemplatesPage from '../ApplicationTemplatesPage.vue'
import ApplicationTemplatePreviewDialog from '@/components/molecules/ApplicationTemplatePreviewDialog.vue'
import { createTestApp } from '@/__tests__/app'
import { confirmPopconfirm, findButton, shownMessages } from '@/__tests__/dom'
import { createApplicationTemplate, createHttpError } from '@/__tests__/factories'
import {
  addApplicationTemplate,
  confirmApplicationTemplateUpload,
  deleteApplicationTemplate,
  getApplicationTemplates,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { uploadFileToStorage } from '@/utils/storage'

vi.mock('@/api/generated/endpoints/application-templates/application-templates')
vi.mock('@/utils/storage')

const templates = [
  createApplicationTemplate({ id: 'template-1', name: 'Wniosek o urlop', status: 'DRAFT' }),
  createApplicationTemplate({
    id: 'template-2',
    name: 'Wniosek o stypendium',
    status: 'PUBLISHED',
  }),
  createApplicationTemplate({ id: 'template-3', name: 'Podanie', status: 'NOT_UPLOADED' }),
]

async function mountPage() {
  const { router, global } = await createTestApp('/admin/application-templates')
  const wrapper = mount(ApplicationTemplatesPage, {
    global: { ...global, stubs: { ...global.stubs, ApplicationTemplatePreviewDialog: true } },
    attachTo: document.body,
  })
  await flushPromises()
  return { router, wrapper }
}

function findItemButton(wrapper: VueWrapper, itemIndex: number, text: string) {
  const item = wrapper.findAll('.template-item')[itemIndex]!
  return item.findAll('button').find((button) => button.text() === text)
}

async function selectFile(wrapper: VueWrapper, file: File) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: [file] })
  await input.trigger('change')
  await flushPromises()
}

describe('ApplicationTemplatesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getApplicationTemplates).mockResolvedValue(templates)
  })

  it('lists templates with their status', async () => {
    const { wrapper } = await mountPage()

    expect(
      wrapper.findAll('.template-item').map((item) => ({
        name: item.find('.template-name').text(),
        status: item.find('.el-tag').text(),
      })),
    ).toEqual([
      { name: 'Wniosek o urlop', status: 'Szkic' },
      { name: 'Wniosek o stypendium', status: 'Opublikowany' },
      { name: 'Podanie', status: 'Niewczytany' },
    ])
    expect(findButton('Dodaj')).toBeUndefined()
  })

  it('does not claim there are no templates while they are being loaded', async () => {
    let finishLoading: ((loadedTemplates: typeof templates) => void) | undefined
    vi.mocked(getApplicationTemplates).mockReturnValue(
      new Promise((resolve) => (finishLoading = resolve)),
    )

    const { wrapper } = await mountPage()
    expect(wrapper.text()).not.toContain('Brak szablonów wniosków.')

    finishLoading?.([])
    await flushPromises()
    expect(wrapper.text()).toContain('Brak szablonów wniosków.')
  })

  it('does not offer a preview of a template whose file was not uploaded', async () => {
    const { wrapper } = await mountPage()

    expect(findItemButton(wrapper, 0, 'Pokaż podgląd')).toBeDefined()
    expect(findItemButton(wrapper, 2, 'Pokaż podgląd')).toBeUndefined()
  })

  it('informs that there are no templates', async () => {
    vi.mocked(getApplicationTemplates).mockResolvedValue([])

    const { wrapper } = await mountPage()

    expect(wrapper.text()).toContain('Brak szablonów wniosków.')
  })

  it('reports templates that could not be loaded', async () => {
    vi.mocked(getApplicationTemplates).mockRejectedValue(createHttpError(500))

    await mountPage()

    expect(shownMessages('error')).toEqual(['Nie udało się pobrać szablonów wniosków.'])
  })

  it('opens the clicked template', async () => {
    const { router, wrapper } = await mountPage()

    await wrapper.findAll('.template-item')[1]!.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.fullPath).toBe('/admin/application-templates/template-2')
  })

  it('previews a template without opening it', async () => {
    const { router, wrapper } = await mountPage()
    const previewDialog = wrapper.findComponent(ApplicationTemplatePreviewDialog)
    expect(previewDialog.props('modelValue')).toBe(false)

    await findItemButton(wrapper, 1, 'Pokaż podgląd')!.trigger('click')
    await flushPromises()

    expect(previewDialog.props()).toEqual({ modelValue: true, templateId: 'template-2' })
    expect(router.currentRoute.value.name).toBe('ApplicationTemplatesPage')
  })

  it('deletes a template after confirmation without opening it', async () => {
    const { router, wrapper } = await mountPage()

    await findItemButton(wrapper, 0, 'Usuń')!.trigger('click')
    expect(deleteApplicationTemplate).not.toHaveBeenCalled()
    await confirmPopconfirm()
    await flushPromises()

    expect(deleteApplicationTemplate).toHaveBeenCalledExactlyOnceWith('template-1')
    expect(shownMessages('success')).toEqual(['Szablon został usunięty.'])
    expect(wrapper.findAll('.template-name').map((name) => name.text())).toEqual([
      'Wniosek o stypendium',
      'Podanie',
    ])
    expect(router.currentRoute.value.name).toBe('ApplicationTemplatesPage')
  })

  it('keeps the template and reports an error when deleting fails', async () => {
    vi.mocked(deleteApplicationTemplate).mockRejectedValue(createHttpError(500))
    const { wrapper } = await mountPage()

    await findItemButton(wrapper, 0, 'Usuń')!.trigger('click')
    await confirmPopconfirm()
    await flushPromises()

    expect(shownMessages('error')).toEqual(['Nie udało się usunąć szablonu.'])
    expect(wrapper.findAll('.template-item')).toHaveLength(3)
  })

  it('uploads a template named after the file and opens it', async () => {
    const uploadTarget = { id: 'template-9', url: 'https://storage.example.com', fields: {} }
    vi.mocked(addApplicationTemplate).mockResolvedValue(uploadTarget)
    const { router, wrapper } = await mountPage()

    await findButton('Dodaj szablon')!.trigger('click')
    await selectFile(wrapper, new File(['docx'], 'Wniosek o przepisanie oceny.DOCX'))
    await findButton('Dodaj')!.trigger('click')
    await flushPromises()

    expect(addApplicationTemplate).toHaveBeenCalledExactlyOnceWith(
      { name: 'Wniosek o przepisanie oceny' },
      { signal: expect.any(AbortSignal) },
    )
    expect(vi.mocked(uploadFileToStorage).mock.calls[0]?.[0]).toEqual(uploadTarget)
    expect(confirmApplicationTemplateUpload).toHaveBeenCalledOnce()
    expect(router.currentRoute.value.fullPath).toBe('/admin/application-templates/template-9')
    expect(findButton('Dodaj')).toBeUndefined()
  })

  it('cancels a running upload when the dialog is closed', async () => {
    vi.mocked(addApplicationTemplate).mockReturnValueOnce(new Promise(() => {}))
    const { wrapper } = await mountPage()
    await findButton('Dodaj szablon')!.trigger('click')
    await selectFile(wrapper, new File(['docx'], 'Wniosek.docx'))
    await findButton('Dodaj')!.trigger('click')
    const signal = vi.mocked(addApplicationTemplate).mock.calls[0]?.[1]?.signal
    expect(signal?.aborted).toBe(false)

    await findButton('Anuluj')!.trigger('click')

    expect(signal?.aborted).toBe(true)
  })

  it('does not upload a template without a file', async () => {
    const { router } = await mountPage()

    await findButton('Dodaj szablon')!.trigger('click')
    await findButton('Dodaj')!.trigger('click')
    await flushPromises()

    expect(shownMessages('warning')).toEqual(['Wybierz plik szablonu.'])
    expect(addApplicationTemplate).not.toHaveBeenCalled()
    expect(router.currentRoute.value.name).toBe('ApplicationTemplatesPage')
  })

  it('forgets the chosen file when the upload dialog is opened again', async () => {
    const { wrapper } = await mountPage()
    await findButton('Dodaj szablon')!.trigger('click')
    await selectFile(wrapper, new File(['docx'], 'Wniosek.docx'))
    await findButton('Anuluj')!.trigger('click')

    await findButton('Dodaj szablon')!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.selected-file-name').exists()).toBe(false)
    expect((wrapper.find('.el-dialog input[type="text"]').element as HTMLInputElement).value).toBe(
      '',
    )
  })

  it('reloads templates after the upload dialog is closed', async () => {
    await mountPage()
    await findButton('Dodaj szablon')!.trigger('click')
    await flushPromises()
    expect(getApplicationTemplates).toHaveBeenCalledTimes(1)

    await findButton('Anuluj')!.trigger('click')
    await flushPromises()

    expect(getApplicationTemplates).toHaveBeenCalledTimes(2)
  })
})
