import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GeneratePdfForm from '../GeneratePdfForm.vue'
import type { PublishedApplicationTemplate } from '@/api/generated/model'

function template(id: string, description: string | null = null): PublishedApplicationTemplate {
  return { id, name: `Wniosek ${id}`, description, fields: [] }
}

const templates = [template('a', 'Wniosek o urlop.'), template('b'), template('c')]

function mountForm(
  searchResults: Array<PublishedApplicationTemplate> | null = null,
  isSearching = false,
) {
  return mount(GeneratePdfForm, {
    props: { templates, searchResults, isSearching },
    global: {
      stubs: {
        ElForm: { template: '<form><slot /></form>', methods: { clearValidate() {} } },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: true,
        ElButton: true,
        ElSelect: {
          template:
            '<div class="select" :data-no-data-text="noDataText" :data-loading="loading"><input class="select-query" @input="remoteMethod($event.target.value)" /><slot /></div>',
          props: ['modelValue', 'remoteMethod', 'noDataText', 'loading'],
        },
        ElOption: {
          template: '<div class="option" :data-value="value"><slot /></div>',
          props: ['value', 'label'],
        },
        ElTooltip: {
          template: '<span class="tooltip" :data-content="content"><slot /></span>',
          props: ['content'],
        },
        ElSwitch: {
          template:
            '<input class="ai-switch" type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
          props: ['modelValue'],
        },
      },
    },
  })
}

function optionValues(wrapper: ReturnType<typeof mountForm>) {
  return wrapper.findAll('.option').map((option) => option.attributes('data-value'))
}

describe('GeneratePdfForm', () => {
  it('emits query typed into the template select without trimming', async () => {
    const wrapper = mountForm()

    await wrapper.find('.select-query').setValue('urlop ')

    expect(wrapper.emitted('search')).toEqual([['urlop ']])
  })

  it('lists all templates without search', () => {
    const wrapper = mountForm()

    expect(optionValues(wrapper)).toEqual(['a', 'b', 'c'])
  })

  it('lists search results in the given order', () => {
    const wrapper = mountForm([templates[2]!, templates[0]!])

    expect(optionValues(wrapper)).toEqual(['c', 'a'])
  })

  it('updates AI assisted search when the switch is toggled', async () => {
    const wrapper = mountForm()

    await wrapper.find('.ai-switch').setValue(true)

    expect(wrapper.emitted('update:aiAssisted')).toEqual([[true]])
  })

  it('shows template description as a tooltip', () => {
    const wrapper = mountForm()

    expect(wrapper.find('.tooltip').attributes('data-content')).toBe('Wniosek o urlop.')
  })

  it('informs when no template matches', () => {
    const wrapper = mountForm([])

    expect(optionValues(wrapper)).toEqual([])
    expect(wrapper.find('.select').attributes('data-no-data-text')).toBe(
      'Nie znaleziono pasujących szablonów.',
    )
  })

  it('shows loading state in the template select while searching', () => {
    const wrapper = mountForm([], true)

    expect(wrapper.find('.select').attributes('data-loading')).toBe('true')
  })
})
