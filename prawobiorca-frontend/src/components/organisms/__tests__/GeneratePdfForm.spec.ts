import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GeneratePdfForm from '../GeneratePdfForm.vue'
import type { PublishedApplicationTemplate } from '@/api/generated/model'

function template(id: string, description: string | null = null): PublishedApplicationTemplate {
  return { id, name: `Wniosek ${id}`, description, fields: [] }
}

const templates = [template('a', 'Wniosek o urlop.'), template('b'), template('c')]

function mountForm(scores: Record<string, number> | null = null) {
  return mount(GeneratePdfForm, {
    props: { templates, scores },
    global: {
      stubs: {
        ElForm: { template: '<form><slot /></form>', methods: { clearValidate() {} } },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: true,
        ElButton: true,
        ElSelect: {
          template:
            '<div class="select" :data-no-data-text="noDataText"><input class="select-query" @input="remoteMethod($event.target.value)" /><slot /></div>',
          props: ['modelValue', 'remoteMethod', 'noDataText'],
        },
        ElOption: {
          template: '<div class="option" :data-value="value"><slot /></div>',
          props: ['value', 'label'],
        },
        ElTooltip: {
          template: '<span class="tooltip" :data-content="content"><slot /></span>',
          props: ['content'],
        },
      },
    },
  })
}

function optionValues(wrapper: ReturnType<typeof mountForm>) {
  return wrapper.findAll('.option').map((option) => option.attributes('data-value'))
}

describe('GeneratePdfForm', () => {
  it('emits trimmed query typed into the template select', async () => {
    const wrapper = mountForm()

    await wrapper.find('.select-query').setValue('  urlop dziekański  ')

    expect(wrapper.emitted('search')).toEqual([['urlop dziekański']])
  })

  it('lists all templates without search', () => {
    const wrapper = mountForm()

    expect(optionValues(wrapper)).toEqual(['a', 'b', 'c'])
    expect(wrapper.find('.template-option-score').exists()).toBe(false)
  })

  it('lists only matching templates ordered by score', () => {
    const wrapper = mountForm({ a: 0.6, c: 0.9 })

    expect(optionValues(wrapper)).toEqual(['c', 'a'])
    expect(wrapper.find('.option').text()).toContain('0.900')
  })

  it('shows template description as a tooltip', () => {
    const wrapper = mountForm()

    expect(wrapper.find('.tooltip').attributes('data-content')).toBe('Wniosek o urlop.')
  })

  it('informs when no template matches', () => {
    const wrapper = mountForm({})

    expect(optionValues(wrapper)).toEqual([])
    expect(wrapper.find('.select').attributes('data-no-data-text')).toBe(
      'Nie znaleziono pasujących szablonów.',
    )
  })
})
