import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ApplicationTemplateEditor from '../ApplicationTemplateEditor.vue'
import ApplicationTemplatePreviewDialog from '@/components/molecules/ApplicationTemplatePreviewDialog.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton, findOption, mockLinkClicks, shownMessages } from '@/__tests__/dom'
import {
  createApplicationTemplate,
  createFailingRequest,
  createHttpError,
  createOrganizations,
  createTemplateField,
} from '@/__tests__/factories'
import {
  getAdminApplicationTemplate,
  getAdminApplicationTemplateDownloadUrl,
  publishApplicationTemplate,
  regenerateApplicationTemplateDescription,
  unpublishApplicationTemplate,
  updateApplicationTemplate,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { useOrganizationsStore } from '@/stores/organizations'
import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/application-templates/application-templates')

async function mountEditor(template: ApplicationTemplateRepresentation) {
  const { global } = await createTestApp()
  useOrganizationsStore().organizations = createOrganizations()
  return mount(ApplicationTemplateEditor, {
    props: { template },
    global: {
      ...global,
      stubs: { ...global.stubs, MdEditorV3: true, ApplicationTemplatePreviewDialog: true },
    },
    attachTo: document.body,
  })
}

async function clickButton(text: string) {
  await findButton(text)!.trigger('click')
  await flushPromises()
}

function findFieldSetting(wrapper: VueWrapper, label: string) {
  return wrapper
    .findAll('.el-collapse-item .el-form-item')
    .find((item) => item.find('label').text() === label)
}

function savedField() {
  return vi.mocked(updateApplicationTemplate).mock.calls[0]?.[1].fields[0]
}

describe('ApplicationTemplateEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(updateApplicationTemplate).mockImplementation((_id, details) =>
      Promise.resolve(createApplicationTemplate({ name: details.name })),
    )
  })

  describe('draft', () => {
    it('saves the edited name, description and fields', async () => {
      const field = createTemplateField()
      const template = createApplicationTemplate({
        fields: [field],
        organizationId: 'pwr',
        suborganizationId: 'w10',
      })
      const wrapper = await mountEditor(template)

      await wrapper.find('.name-input input').setValue('  Wniosek o urlop zdrowotny ')
      await wrapper.find('textarea').setValue(' Wniosek o urlop z powodu choroby. ')
      await clickButton('Zapisz')

      expect(updateApplicationTemplate).toHaveBeenCalledExactlyOnceWith('template-1', {
        name: 'Wniosek o urlop zdrowotny',
        instructions: 'Sporządź wniosek do Dziekana.',
        description: 'Wniosek o urlop z powodu choroby.',
        organizationId: 'pwr',
        suborganizationId: 'w10',
        fields: [field],
      })
      expect(shownMessages('success')).toEqual(['Szablon został zapisany.'])
      expect(wrapper.emitted('updated')).toEqual([
        [createApplicationTemplate({ name: 'Wniosek o urlop zdrowotny' })],
      ])
    })

    it('saves a general template without organization', async () => {
      await mountEditor(createApplicationTemplate())

      await clickButton('Zapisz')

      expect(updateApplicationTemplate).toHaveBeenCalledWith(
        'template-1',
        expect.objectContaining({ organizationId: null, suborganizationId: null }),
      )
    })

    it('assigns the template to the chosen organization and clears its suborganization', async () => {
      await mountEditor(
        createApplicationTemplate({ organizationId: 'pwr', suborganizationId: 'w10' }),
      )

      await findOption('Uniwersytet Wrocławski')!.trigger('click')
      await clickButton('Zapisz')

      expect(updateApplicationTemplate).toHaveBeenCalledWith(
        'template-1',
        expect.objectContaining({ organizationId: 'uwr', suborganizationId: null }),
      )
    })

    it('reports a template that could not be saved', async () => {
      vi.mocked(updateApplicationTemplate).mockRejectedValue(createHttpError(422))
      const wrapper = await mountEditor(createApplicationTemplate())

      await clickButton('Zapisz')

      expect(shownMessages('error')).toEqual([
        'Nie udało się zapisać szablonu. Sprawdź nazwę, regexy, opcje list i wartości domyślne.',
      ])
      expect(shownMessages('success')).toEqual([])
      expect(wrapper.emitted('updated')).toBeUndefined()
    })

    it('saves the template before publishing it', async () => {
      const publishedTemplate = createApplicationTemplate({ status: 'PUBLISHED' })
      vi.mocked(publishApplicationTemplate).mockResolvedValue(publishedTemplate)
      const wrapper = await mountEditor(createApplicationTemplate())

      await clickButton('Zapisz i opublikuj')

      expect(updateApplicationTemplate).toHaveBeenCalledOnce()
      expect(publishApplicationTemplate).toHaveBeenCalledExactlyOnceWith('template-1')
      expect(shownMessages('success')).toEqual(['Szablon został opublikowany.'])
      expect(wrapper.emitted('updated')?.[1]).toEqual([publishedTemplate])
    })

    it('does not publish a template that could not be saved', async () => {
      vi.mocked(updateApplicationTemplate).mockRejectedValue(createHttpError(422))
      await mountEditor(createApplicationTemplate())

      await clickButton('Zapisz i opublikuj')

      expect(publishApplicationTemplate).not.toHaveBeenCalled()
      expect(shownMessages('success')).toEqual([])
    })

    it('asks for AI instructions when the template cannot be published without them', async () => {
      vi.mocked(publishApplicationTemplate).mockRejectedValue(createHttpError(409))
      await mountEditor(createApplicationTemplate({ instructions: null }))

      await clickButton('Zapisz i opublikuj')

      expect(shownMessages('error')).toEqual(['Uzupełnij instrukcje dla AI przed publikacją.'])
    })

    it('saves the template before starting description generation', async () => {
      const generatingTemplate = createApplicationTemplate({ descriptionStatus: 'IN_PROGRESS' })
      vi.mocked(getAdminApplicationTemplate).mockResolvedValue(generatingTemplate)
      const wrapper = await mountEditor(
        createApplicationTemplate({ description: 'Wniosek o urlop.' }),
      )

      await clickButton('Wygeneruj opis przez AI')

      expect(updateApplicationTemplate).toHaveBeenCalledWith(
        'template-1',
        expect.objectContaining({ description: 'Wniosek o urlop.' }),
      )
      expect(regenerateApplicationTemplateDescription).toHaveBeenCalledExactlyOnceWith('template-1')
      expect(shownMessages('success')).toEqual(['Generowanie opisu zostało rozpoczęte.'])
      expect(wrapper.emitted('updated')?.[1]).toEqual([generatingTemplate])
    })

    it('does not start description generation when saving fails', async () => {
      vi.mocked(updateApplicationTemplate).mockRejectedValue(createHttpError(422))
      await mountEditor(createApplicationTemplate())

      await clickButton('Wygeneruj opis przez AI')

      expect(regenerateApplicationTemplateDescription).not.toHaveBeenCalled()
    })

    it('explains why description generation could not be started', async () => {
      vi.mocked(regenerateApplicationTemplateDescription).mockRejectedValue(createHttpError(409))
      await mountEditor(createApplicationTemplate())

      await clickButton('Wygeneruj opis przez AI')

      expect(shownMessages('error')).toEqual([
        'Opis jest już generowany lub szablon nie jest szkicem.',
      ])
      expect(getAdminApplicationTemplate).not.toHaveBeenCalled()
    })

    it.each([
      [
        'Zapisz',
        (request: Promise<never>) =>
          vi.mocked(updateApplicationTemplate).mockReturnValueOnce(request),
      ],
      [
        'Zapisz i opublikuj',
        (request: Promise<never>) =>
          vi.mocked(publishApplicationTemplate).mockReturnValueOnce(request),
      ],
      [
        'Wygeneruj opis przez AI',
        (request: Promise<never>) =>
          vi.mocked(regenerateApplicationTemplateDescription).mockReturnValueOnce(request),
      ],
      [
        'Pobierz szablon',
        (request: Promise<never>) =>
          vi.mocked(getAdminApplicationTemplateDownloadUrl).mockReturnValueOnce(request),
      ],
    ])('shows "%s" as busy until its request ends', async (label, mockRequest) => {
      const { request, fail } = createFailingRequest()
      mockRequest(request)
      await mountEditor(createApplicationTemplate())
      expect(findButton(label)!.classes()).not.toContain('is-loading')

      await clickButton(label)
      expect(findButton(label)!.classes()).toContain('is-loading')

      fail()
      await flushPromises()
      expect(findButton(label)!.classes()).not.toContain('is-loading')
    })

    it('blocks editing while description is generated', async () => {
      const wrapper = await mountEditor(
        createApplicationTemplate({ descriptionStatus: 'IN_PROGRESS' }),
      )

      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
      expect(findButton('Zapisz')!.attributes('disabled')).toBeDefined()
      expect(findButton('Zapisz i opublikuj')!.attributes('disabled')).toBeDefined()
      expect(wrapper.find('textarea').attributes('disabled')).toBeDefined()
      expect(wrapper.find('.description-generation').text()).toBe('Generowanie opisu')
    })

    it('informs that description generation failed and allows another attempt', async () => {
      const wrapper = await mountEditor(createApplicationTemplate({ descriptionStatus: 'FAILED' }))

      expect(wrapper.find('.description-generation .el-tag').text()).toBe('Błąd generowania opisu')
      expect(findButton('Wygeneruj opis przez AI')).toBeDefined()
      expect(wrapper.find('textarea').attributes('disabled')).toBeUndefined()
    })

    it('shows the form of the template fields', async () => {
      const wrapper = await mountEditor(
        createApplicationTemplate({
          fields: [
            createTemplateField({ name: 'index_number' }),
            createTemplateField({ name: 'semester' }),
          ],
        }),
      )

      expect(wrapper.findAll('.field-name').map((name) => name.text())).toEqual([
        'index_number',
        'semester',
      ])
    })

    it('informs that the template has no fields', async () => {
      const wrapper = await mountEditor(createApplicationTemplate())

      expect(wrapper.text()).toContain('Szablon nie zawiera pól do wypełnienia.')
    })

    it('shows the data of a template loaded in place of the edited one', async () => {
      const wrapper = await mountEditor(createApplicationTemplate())

      await wrapper.setProps({
        template: createApplicationTemplate({ description: 'Wygenerowany opis.' }),
      })

      expect(wrapper.find('textarea').element.value).toBe('Wygenerowany opis.')
    })
  })

  describe('template fields', () => {
    it('saves the edited label, pattern, default value and flags of a field', async () => {
      const wrapper = await mountEditor(
        createApplicationTemplate({
          fields: [createTemplateField({ required: true, passToAi: false })],
        }),
      )

      await findFieldSetting(wrapper, 'Etykieta:')!.find('input').setValue('Nr albumu')
      await findFieldSetting(wrapper, 'Regex walidacji (opcjonalnie):')!
        .find('input')
        .setValue(String.raw`\d{6}`)
      await findFieldSetting(wrapper, 'Wartość domyślna (opcjonalnie):')!
        .find('input')
        .setValue('123456')
      const [requiredCheckbox, passToAiCheckbox] = wrapper.findAll('.field-flags input')
      await requiredCheckbox!.setValue(false)
      await passToAiCheckbox!.setValue(true)
      await clickButton('Zapisz')

      expect(savedField()).toEqual(
        createTemplateField({
          label: 'Nr albumu',
          pattern: String.raw`\d{6}`,
          defaultValue: '123456',
          required: false,
          passToAi: true,
        }),
      )
    })

    it('drops the pattern and the default value when a text field becomes a number', async () => {
      const wrapper = await mountEditor(
        createApplicationTemplate({
          fields: [createTemplateField({ pattern: String.raw`\d{6}`, defaultValue: '123456' })],
        }),
      )

      await findOption('Liczba')!.trigger('click')
      await clickButton('Zapisz')

      expect(findFieldSetting(wrapper, 'Regex walidacji (opcjonalnie):')).toBeUndefined()
      expect(savedField()).toMatchObject({ fieldType: 'NUMBER', pattern: null, defaultValue: null })
    })

    it('drops the options and the default value when a select field becomes a text', async () => {
      const wrapper = await mountEditor(
        createApplicationTemplate({
          fields: [
            createTemplateField({
              fieldType: 'SELECT',
              options: ['zimowy', 'letni'],
              defaultValue: 'letni',
            }),
          ],
        }),
      )
      expect(findFieldSetting(wrapper, 'Opcje listy:')).toBeDefined()

      await findOption('Tekst')!.trigger('click')
      await clickButton('Zapisz')

      expect(findFieldSetting(wrapper, 'Opcje listy:')).toBeUndefined()
      expect(savedField()).toMatchObject({ fieldType: 'TEXT', options: [], defaultValue: null })
    })

    it('offers the options of a select field as its default value', async () => {
      await mountEditor(
        createApplicationTemplate({
          fields: [createTemplateField({ fieldType: 'SELECT', options: ['zimowy', 'letni'] })],
        }),
      )

      await findOption('letni')!.trigger('click')
      await clickButton('Zapisz')

      expect(savedField()).toMatchObject({ options: ['zimowy', 'letni'], defaultValue: 'letni' })
    })

    it('offers a date picker as the default value of a date field', async () => {
      const wrapper = await mountEditor(
        createApplicationTemplate({ fields: [createTemplateField({ fieldType: 'DATE' })] }),
      )

      expect(
        findFieldSetting(wrapper, 'Wartość domyślna (opcjonalnie):')!
          .find('.el-date-editor')
          .exists(),
      ).toBe(true)
    })

    it('does not change the loaded template until it is saved', async () => {
      const template = createApplicationTemplate({
        fields: [createTemplateField({ fieldType: 'SELECT', options: ['zimowy', 'letni'] })],
      })
      await mountEditor(template)

      await findOption('Tekst')!.trigger('click')

      expect(template.fields[0]?.options).toEqual(['zimowy', 'letni'])
    })
  })

  describe('published template', () => {
    const publishedTemplate = createApplicationTemplate({ status: 'PUBLISHED' })

    it('is read-only until its publication is withdrawn', async () => {
      const wrapper = await mountEditor(publishedTemplate)

      expect(wrapper.find('h2').text()).toBe('Wniosek o urlop dziekański')
      expect(wrapper.find('.name-input').exists()).toBe(false)
      expect(wrapper.find('.el-alert').text()).toBe(
        'Szablon jest opublikowany. Wycofaj publikację, aby go edytować.',
      )
      expect(wrapper.find('textarea').attributes('disabled')).toBeDefined()
      expect(findButton('Zapisz')).toBeUndefined()
      expect(findButton('Zapisz i opublikuj')).toBeUndefined()
      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
    })

    it('withdraws the publication', async () => {
      const draftTemplate = createApplicationTemplate({ status: 'DRAFT' })
      vi.mocked(unpublishApplicationTemplate).mockResolvedValue(draftTemplate)
      const wrapper = await mountEditor(publishedTemplate)

      await clickButton('Wycofaj publikację')

      expect(unpublishApplicationTemplate).toHaveBeenCalledExactlyOnceWith('template-1')
      expect(updateApplicationTemplate).not.toHaveBeenCalled()
      expect(shownMessages('success')).toEqual(['Publikacja szablonu została wycofana.'])
      expect(wrapper.emitted('updated')).toEqual([[draftTemplate]])
    })

    it('shows withdrawing the publication as busy until its request ends', async () => {
      const { request, fail } = createFailingRequest()
      vi.mocked(unpublishApplicationTemplate).mockReturnValueOnce(request)
      await mountEditor(publishedTemplate)

      await clickButton('Wycofaj publikację')
      expect(findButton('Wycofaj publikację')!.classes()).toContain('is-loading')

      fail()
      await flushPromises()
      expect(findButton('Wycofaj publikację')!.classes()).not.toContain('is-loading')
    })

    it('reports a publication that could not be withdrawn', async () => {
      vi.mocked(unpublishApplicationTemplate).mockRejectedValue(createHttpError(500))
      const wrapper = await mountEditor(publishedTemplate)

      await clickButton('Wycofaj publikację')

      expect(shownMessages('error')).toEqual(['Nie udało się wycofać publikacji szablonu.'])
      expect(wrapper.emitted('updated')).toBeUndefined()
    })
  })

  describe('template file', () => {
    it('downloads the template file', async () => {
      const clickedUrls = mockLinkClicks()
      vi.mocked(getAdminApplicationTemplateDownloadUrl).mockResolvedValue(
        'https://storage.example.com/template.docx',
      )
      await mountEditor(createApplicationTemplate())

      await clickButton('Pobierz szablon')

      expect(getAdminApplicationTemplateDownloadUrl).toHaveBeenCalledExactlyOnceWith('template-1')
      expect(clickedUrls).toEqual(['https://storage.example.com/template.docx'])
    })

    it('reports a template file that could not be downloaded', async () => {
      const clickedUrls = mockLinkClicks()
      vi.mocked(getAdminApplicationTemplateDownloadUrl).mockRejectedValue(createHttpError(500))
      await mountEditor(createApplicationTemplate())

      await clickButton('Pobierz szablon')

      expect(shownMessages('error')).toEqual(['Nie udało się pobrać szablonu.'])
      expect(clickedUrls).toEqual([])
    })

    it('opens the preview of the template file', async () => {
      const wrapper = await mountEditor(createApplicationTemplate())
      const previewDialog = wrapper.findComponent(ApplicationTemplatePreviewDialog)
      expect(previewDialog.props('modelValue')).toBe(false)

      await clickButton('Pokaż podgląd')

      expect(previewDialog.props()).toEqual({ modelValue: true, templateId: 'template-1' })
    })

    it('offers only deleting a template whose file was not uploaded', async () => {
      const wrapper = await mountEditor(createApplicationTemplate({ status: 'NOT_UPLOADED' }))

      expect(wrapper.find('.el-alert').text()).toBe(
        'Plik szablonu nie został wczytany. Usuń szablon i dodaj go ponownie.',
      )
      expect(wrapper.find('form').exists()).toBe(false)
      expect(wrapper.findAll('.editor-actions button')).toHaveLength(0)
    })
  })
})
