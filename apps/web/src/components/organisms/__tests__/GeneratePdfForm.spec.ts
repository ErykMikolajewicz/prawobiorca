import { describe, it, expect, vi, afterEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import GeneratePdfForm from '../GeneratePdfForm.vue'
import { findOption, page } from '@/__tests__/dom'
import { createPublishedTemplate, createTemplateField } from '@/__tests__/factories'
import type { PublishedApplicationTemplate } from '@/api/generated/model'

const leaveTemplate = createPublishedTemplate({
  id: 'leave',
  name: 'Wniosek o urlop',
  description: 'Wniosek o urlop dziekański.',
  fields: [
    createTemplateField({
      name: 'index_number',
      label: 'Numer indeksu',
      pattern: String.raw`\d{6}`,
    }),
    createTemplateField({
      name: 'semester',
      label: 'Semestr',
      fieldType: 'SELECT',
      required: false,
      options: ['zimowy', 'letni'],
      defaultValue: 'letni',
    }),
    createTemplateField({
      name: 'ects',
      label: 'Punkty ECTS',
      fieldType: 'NUMBER',
      required: false,
    }),
    createTemplateField({
      name: 'start_date',
      label: 'Data rozpoczęcia',
      fieldType: 'DATE',
      required: false,
    }),
  ],
})
const scholarshipTemplate = createPublishedTemplate({
  id: 'scholarship',
  name: 'Wniosek o stypendium',
  fields: [createTemplateField({ name: 'semester', label: 'Semestr', defaultValue: '3' })],
})
const plainTemplate = createPublishedTemplate({ id: 'plain', name: 'Podanie' })
const templates = [leaveTemplate, scholarshipTemplate, plainTemplate]

function mountForm(props: {
  searchResults?: Array<PublishedApplicationTemplate> | null
  isSearching?: boolean
}) {
  return mount(GeneratePdfForm, {
    props: { templates, ...props },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

function optionLabels() {
  return page()
    .findAll('.el-select-dropdown__item')
    .map((option) => option.text())
}

function findField(wrapper: VueWrapper, label: string) {
  return wrapper
    .findAll('.el-form-item')
    .find((item) => item.find('label').exists() && item.find('label').text() === label)
}

function fieldLabels(wrapper: VueWrapper) {
  return wrapper.findAll('.el-form-item__label').map((label) => label.text())
}

async function chooseTemplate(name: string) {
  await findOption(name)!.trigger('click')
}

async function submit(wrapper: VueWrapper) {
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

function shownErrors(wrapper: VueWrapper) {
  return wrapper.findAll('.el-form-item__error').map((error) => error.text())
}

describe('GeneratePdfForm', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  describe('template choice', () => {
    it('lists all templates without search', () => {
      mountForm({})

      expect(optionLabels()).toEqual(['Wniosek o urlop', 'Wniosek o stypendium', 'Podanie'])
    })

    it('lists search results in the given order', () => {
      mountForm({ searchResults: [plainTemplate, leaveTemplate] })

      expect(optionLabels()).toEqual(['Podanie', 'Wniosek o urlop'])
    })

    it('informs when no template matches', () => {
      mountForm({ searchResults: [] })

      expect(optionLabels()).toEqual([])
      expect(page().find('.el-select-dropdown').text()).toBe('Nie znaleziono pasujących szablonów.')
    })

    it('shows a loading state in the template select while searching', () => {
      mountForm({ searchResults: [], isSearching: true })

      expect(page().find('.el-select-dropdown').text()).toBe('Wyszukiwanie szablonów...')
    })

    it('emits the query typed into the template select without trimming', async () => {
      vi.useFakeTimers()
      const wrapper = mountForm({})

      await wrapper.find('.el-select input').setValue('urlop ')
      await vi.advanceTimersByTimeAsync(1000)

      expect(wrapper.emitted('search')).toEqual([['urlop ']])
    })

    it('updates AI assisted search when the switch is toggled', async () => {
      const wrapper = mountForm({})

      await wrapper.find('.el-switch input').trigger('click')

      expect(wrapper.emitted('update:aiAssisted')).toEqual([[true]])
    })
  })

  describe('template fields', () => {
    it('shows no template fields until a template is chosen', () => {
      const wrapper = mountForm({})

      expect(fieldLabels(wrapper)).toEqual([
        'Rodzaj wniosku:',
        'Opisz swoją sytuację lub cel pisma:',
      ])
    })

    it('shows the fields of the chosen template with an input matching their type', async () => {
      const wrapper = mountForm({})

      await chooseTemplate('Wniosek o urlop')

      expect(fieldLabels(wrapper)).toEqual([
        'Rodzaj wniosku:',
        'Numer indeksu:',
        'Semestr:',
        'Punkty ECTS:',
        'Data rozpoczęcia:',
        'Opisz swoją sytuację lub cel pisma:',
      ])
      expect(findField(wrapper, 'Numer indeksu:')!.find('input').attributes('type')).toBe('text')
      expect(findField(wrapper, 'Semestr:')!.find('.el-select').exists()).toBe(true)
      expect(findField(wrapper, 'Punkty ECTS:')!.find('input').attributes('type')).toBe('number')
      expect(findField(wrapper, 'Data rozpoczęcia:')!.find('.el-date-editor').exists()).toBe(true)
      expect(optionLabels()).toEqual(expect.arrayContaining(['zimowy', 'letni']))
    })

    it('replaces the fields and their values when another template is chosen', async () => {
      const wrapper = mountForm({})
      await chooseTemplate('Wniosek o urlop')
      await findField(wrapper, 'Numer indeksu:')!.find('input').setValue('123456')

      await chooseTemplate('Wniosek o stypendium')
      await wrapper.find('textarea').setValue('Proszę o stypendium.')
      await submit(wrapper)

      expect(wrapper.emitted('generate-pdf')).toEqual([
        [
          {
            templateId: 'scholarship',
            description: 'Proszę o stypendium.',
            fieldValues: { semester: '3' },
          },
        ],
      ])
    })

    it('forgets the chosen template when it is no longer available', async () => {
      const wrapper = mountForm({})
      await chooseTemplate('Wniosek o urlop')

      await wrapper.setProps({ templates: [plainTemplate] })
      await wrapper.find('textarea').setValue('Proszę o urlop.')
      await submit(wrapper)

      expect(fieldLabels(wrapper)).not.toContain('Numer indeksu:')
      expect(wrapper.emitted('generate-pdf')).toBeUndefined()
      await vi.waitFor(() => expect(shownErrors(wrapper)).toEqual(['Wybierz szablon wniosku.']))
    })

    it('keeps the chosen template when the list is reloaded with it', async () => {
      const wrapper = mountForm({})
      await chooseTemplate('Wniosek o urlop')
      await findField(wrapper, 'Numer indeksu:')!.find('input').setValue('123456')

      await wrapper.setProps({ templates: [leaveTemplate, plainTemplate] })

      expect(
        (findField(wrapper, 'Numer indeksu:')!.find('input').element as HTMLInputElement).value,
      ).toBe('123456')
    })
  })

  describe('submission', () => {
    it('emits the application with the filled and default field values', async () => {
      const wrapper = mountForm({})

      await chooseTemplate('Wniosek o urlop')
      await findField(wrapper, 'Numer indeksu:')!.find('input').setValue('123456')
      await findField(wrapper, 'Punkty ECTS:')!.find('input').setValue('30')
      await wrapper.find('textarea').setValue('Proszę o urlop z powodu choroby.')
      await submit(wrapper)

      expect(wrapper.emitted('generate-pdf')).toEqual([
        [
          {
            templateId: 'leave',
            description: 'Proszę o urlop z powodu choroby.',
            fieldValues: { index_number: '123456', semester: 'letni', ects: '30', start_date: '' },
          },
        ],
      ])
    })

    it('requires a template and a description', async () => {
      const wrapper = mountForm({})

      await submit(wrapper)

      expect(wrapper.emitted('generate-pdf')).toBeUndefined()
      await vi.waitFor(() =>
        expect(shownErrors(wrapper)).toEqual(['Wybierz szablon wniosku.', 'Opisz swoją sytuację.']),
      )
    })

    it('requires the required fields of the template', async () => {
      const wrapper = mountForm({})

      await chooseTemplate('Wniosek o urlop')
      await wrapper.find('textarea').setValue('Proszę o urlop.')
      await submit(wrapper)

      expect(wrapper.emitted('generate-pdf')).toBeUndefined()
      await vi.waitFor(() => expect(shownErrors(wrapper)).toEqual(['To pole jest wymagane.']))
    })

    it.each(['12345', '1234567', 'a123456'])(
      'rejects the value %s that does not match the whole field pattern',
      async (indexNumber) => {
        const wrapper = mountForm({})

        await chooseTemplate('Wniosek o urlop')
        await findField(wrapper, 'Numer indeksu:')!.find('input').setValue(indexNumber)
        await wrapper.find('textarea').setValue('Proszę o urlop.')
        await submit(wrapper)

        expect(wrapper.emitted('generate-pdf')).toBeUndefined()
        await vi.waitFor(() => expect(shownErrors(wrapper)).toEqual(['Nieprawidłowy format.']))
      },
    )

    it('does not report empty fields right after a template is chosen', async () => {
      const wrapper = mountForm({})

      await chooseTemplate('Wniosek o urlop')
      await flushPromises()

      expect(findField(wrapper, 'Numer indeksu:')!.classes()).not.toContain('is-error')
      expect(findField(wrapper, 'Opisz swoją sytuację lub cel pisma:')!.classes()).not.toContain(
        'is-error',
      )
    })

    it('hides the errors of the previous template after another one is chosen', async () => {
      const wrapper = mountForm({})
      await chooseTemplate('Wniosek o urlop')
      await submit(wrapper)
      await vi.waitFor(() =>
        expect(shownErrors(wrapper)).toEqual(['To pole jest wymagane.', 'Opisz swoją sytuację.']),
      )

      await chooseTemplate('Podanie')

      await vi.waitFor(() => expect(shownErrors(wrapper)).toEqual([]))
    })
  })
})
