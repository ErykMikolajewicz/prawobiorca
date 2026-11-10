import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CasePage from '../CasePage.vue'
import { createTestApp } from '@/__tests__/app'
import {
  confirmPopconfirm,
  findButton,
  findOption,
  mockLinkClicks,
  page,
  shownMessages,
} from '@/__tests__/dom'
import {
  createApplication,
  createCaseDocument,
  createHttpError,
  createPublishedTemplate,
} from '@/__tests__/factories'
import { getPublishedApplicationTemplates } from '@/api/generated/endpoints/application-templates/application-templates'
import {
  deleteApplication,
  deleteCaseDocument,
  generateApplication,
  getCaseApplicationDownloadUrl,
  getCaseApplications,
  getCaseDocuments,
} from '@/api/generated/endpoints/cases/cases'
import { useOrganizationsStore } from '@/stores/organizations'

vi.mock('@/api/generated/endpoints/cases/cases')
vi.mock('@/api/generated/endpoints/application-templates/application-templates')

async function mountPage() {
  const { global } = await createTestApp('/user/cases/case-1')
  const wrapper = mount(CasePage, { global, attachTo: document.body })
  await flushPromises()
  return wrapper
}

async function orderApplication(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  await findOption('Wniosek o urlop dziekański')!.trigger('click')
  await wrapper.find('textarea').setValue('Proszę o urlop z powodu choroby.')
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('CasePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getCaseDocuments).mockResolvedValue([])
    vi.mocked(getCaseApplications).mockResolvedValue([])
    vi.mocked(getPublishedApplicationTemplates).mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('pinned documents', () => {
    it('lists documents pinned to the case from the address', async () => {
      vi.mocked(getCaseDocuments).mockResolvedValue([createCaseDocument()])

      const wrapper = await mountPage()

      expect(getCaseDocuments).toHaveBeenCalledExactlyOnceWith('case-1')
      expect(wrapper.find('.pinned-document').text()).toBe('Regulamin studiów§ 12')
    })

    it('informs that the case has no pinned documents', async () => {
      const wrapper = await mountPage()

      expect(wrapper.text()).toContain('Brak przypiętych artykułów do tej sprawy.')
    })

    it('reports documents that could not be loaded', async () => {
      vi.mocked(getCaseDocuments).mockRejectedValue(createHttpError(500))

      const wrapper = await mountPage()

      expect(shownMessages('error')).toEqual(['Nie udało się pobrać przypiętych dokumentów.'])
      expect(wrapper.text()).toContain('Brak przypiętych artykułów do tej sprawy.')
    })

    it('unpins a document', async () => {
      vi.mocked(getCaseDocuments).mockResolvedValue([
        createCaseDocument({ id: 'document-1', header: '§ 12' }),
        createCaseDocument({ id: 'document-2', header: '§ 13' }),
      ])
      const wrapper = await mountPage()

      await wrapper.find('.pinned-document button[aria-label="Odepnij"]').trigger('click')
      await flushPromises()

      expect(deleteCaseDocument).toHaveBeenCalledExactlyOnceWith('case-1', 'document-1')
      expect(
        wrapper.findAll('.pinned-document').map((card) => card.find('.header').text()),
      ).toEqual(['§ 13'])
    })

    it('keeps the document and reports an error when unpinning fails', async () => {
      vi.mocked(getCaseDocuments).mockResolvedValue([createCaseDocument()])
      vi.mocked(deleteCaseDocument).mockRejectedValue(createHttpError(500))
      const wrapper = await mountPage()

      await wrapper.find('.pinned-document button[aria-label="Odepnij"]').trigger('click')
      await flushPromises()

      expect(shownMessages('error')).toEqual(['Nie udało się odpiąć dokumentu.'])
      expect(wrapper.findAll('.pinned-document')).toHaveLength(1)
    })
  })

  describe('generated applications', () => {
    it('lists applications of the case from the address', async () => {
      vi.mocked(getCaseApplications).mockResolvedValue([
        createApplication({ name: 'Wniosek o urlop zdrowotny' }),
      ])

      const wrapper = await mountPage()

      expect(getCaseApplications).toHaveBeenCalledExactlyOnceWith('case-1')
      expect(wrapper.find('.generated-application .name').text()).toBe('Wniosek o urlop zdrowotny')
    })

    it('reports applications that could not be loaded', async () => {
      vi.mocked(getCaseApplications).mockRejectedValue(createHttpError(500))

      const wrapper = await mountPage()

      expect(shownMessages('error')).toEqual(['Nie udało się pobrać wygenerowanych wniosków.'])
      expect(wrapper.text()).toContain('Brak wygenerowanych wniosków do tej sprawy.')
    })

    it('downloads a generated application', async () => {
      const clickedUrls = mockLinkClicks()
      vi.mocked(getCaseApplications).mockResolvedValue([createApplication()])
      vi.mocked(getCaseApplicationDownloadUrl).mockResolvedValue(
        'https://storage.example.com/wniosek.docx',
      )
      await mountPage()

      await findButton('Pobierz')!.trigger('click')
      await flushPromises()

      expect(getCaseApplicationDownloadUrl).toHaveBeenCalledExactlyOnceWith(
        'case-1',
        'application-1',
      )
      expect(clickedUrls).toEqual(['https://storage.example.com/wniosek.docx'])
    })

    it('reports an application that could not be downloaded', async () => {
      const clickedUrls = mockLinkClicks()
      vi.mocked(getCaseApplications).mockResolvedValue([createApplication()])
      vi.mocked(getCaseApplicationDownloadUrl).mockRejectedValue(createHttpError(404))
      await mountPage()

      await findButton('Pobierz')!.trigger('click')
      await flushPromises()

      expect(shownMessages('error')).toEqual(['Nie udało się pobrać wniosku.'])
      expect(clickedUrls).toEqual([])
    })

    it('deletes an application after confirmation', async () => {
      vi.mocked(getCaseApplications).mockResolvedValue([
        createApplication({ id: 'application-1', name: 'Pierwszy' }),
        createApplication({ id: 'application-2', name: 'Drugi' }),
      ])
      const wrapper = await mountPage()

      await findButton('Usuń')!.trigger('click')
      expect(deleteApplication).not.toHaveBeenCalled()
      await confirmPopconfirm()
      await flushPromises()

      expect(deleteApplication).toHaveBeenCalledExactlyOnceWith('case-1', 'application-1')
      expect(wrapper.findAll('.generated-application .name').map((name) => name.text())).toEqual([
        'Drugi',
      ])
    })

    it('keeps the application and reports an error when deleting fails', async () => {
      vi.mocked(getCaseApplications).mockResolvedValue([createApplication()])
      vi.mocked(deleteApplication).mockRejectedValue(createHttpError(500))
      const wrapper = await mountPage()

      await findButton('Usuń')!.trigger('click')
      await confirmPopconfirm()
      await flushPromises()

      expect(shownMessages('error')).toEqual(['Nie udało się usunąć wniosku.'])
      expect(wrapper.findAll('.generated-application')).toHaveLength(1)
    })

    it('refreshes an application being generated until it is ready', async () => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
      vi.mocked(getCaseApplications)
        .mockResolvedValueOnce([createApplication({ generationStatus: 'IN_PROGRESS' })])
        .mockResolvedValue([createApplication({ generationStatus: 'GENERATED' })])
      const wrapper = await mountPage()
      expect(wrapper.find('.generated-application').text()).toContain('Generowanie')
      expect(findButton('Pobierz')).toBeUndefined()

      await vi.advanceTimersByTimeAsync(5000)
      await flushPromises()

      expect(findButton('Pobierz')).toBeDefined()

      await vi.advanceTimersByTimeAsync(30_000)
      expect(getCaseApplications).toHaveBeenCalledTimes(2)
    })

    it('keeps the list when a background refresh fails', async () => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
      vi.mocked(getCaseApplications)
        .mockResolvedValueOnce([createApplication({ generationStatus: 'IN_PROGRESS' })])
        .mockRejectedValue(createHttpError(503))
      const wrapper = await mountPage()

      await vi.advanceTimersByTimeAsync(5000)
      await flushPromises()

      expect(wrapper.findAll('.generated-application')).toHaveLength(1)
      expect(shownMessages('error')).toEqual([])
    })
  })

  describe('application generation', () => {
    beforeEach(() => {
      vi.mocked(getPublishedApplicationTemplates).mockResolvedValue([createPublishedTemplate()])
    })

    it('orders an application and shows it as being generated', async () => {
      vi.mocked(getCaseApplications)
        .mockResolvedValueOnce([])
        .mockResolvedValue([createApplication({ generationStatus: 'IN_PROGRESS' })])
      const wrapper = await mountPage()

      await orderApplication(wrapper)

      expect(generateApplication).toHaveBeenCalledExactlyOnceWith('case-1', {
        templateId: 'template-1',
        description: 'Proszę o urlop z powodu choroby.',
        fieldValues: {},
      })
      expect(shownMessages('success')).toEqual([
        'Wniosek jest generowany. Pobierzesz go z listy, gdy będzie gotowy.',
      ])
      expect(wrapper.find('.generated-application').text()).toContain('Generowanie')
    })

    it('reports an application that could not be ordered', async () => {
      vi.mocked(generateApplication).mockRejectedValue(createHttpError(503))
      const wrapper = await mountPage()

      await orderApplication(wrapper)

      expect(shownMessages('error')).toEqual([
        'Serwis jest chwilowo niedostępny. Spróbuj ponownie później.',
      ])
      expect(shownMessages('success')).toEqual([])
      expect(getCaseApplications).toHaveBeenCalledTimes(1)
    })
  })

  describe('application templates', () => {
    it('loads templates filtered by the selected organization', async () => {
      const { global } = await createTestApp('/user/cases/case-1')
      useOrganizationsStore().select('pwr', 'w10')

      mount(CasePage, { global })
      await flushPromises()

      expect(getPublishedApplicationTemplates).toHaveBeenCalledWith({
        organizationId: 'pwr',
        suborganizationId: 'w10',
      })
    })

    it('reloads templates when the selected organization changes', async () => {
      await mountPage()

      useOrganizationsStore().select('pwr', '')
      await flushPromises()

      expect(getPublishedApplicationTemplates).toHaveBeenLastCalledWith({
        organizationId: 'pwr',
        suborganizationId: undefined,
      })
    })

    it('offers the loaded templates in the application form', async () => {
      vi.mocked(getPublishedApplicationTemplates).mockResolvedValue([
        createPublishedTemplate({ id: 'a', name: 'Wniosek o stypendium' }),
        createPublishedTemplate({ id: 'b', name: 'Wniosek o urlop' }),
      ])

      await mountPage()

      expect(
        page()
          .findAll('.el-select-dropdown__item')
          .map((option) => option.text()),
      ).toEqual(['Wniosek o stypendium', 'Wniosek o urlop'])
    })
  })
})
