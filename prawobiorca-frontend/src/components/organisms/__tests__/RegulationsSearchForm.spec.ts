import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RegulationsSearchForm from '../RegulationsSearchForm.vue'
import type { RegulationsSearchParams } from '@/domain/regulations'

function mountForm(searchParams: RegulationsSearchParams) {
  return mount(RegulationsSearchForm, {
    props: { searchParams, canUseAdvancedThreshold: false },
    global: {
      stubs: {
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: { template: '<div><slot /></div>' },
        ElRow: { template: '<div><slot /></div>' },
        ElCol: { template: '<div><slot /></div>' },
        ElInput: {
          template:
            '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
          props: ['modelValue'],
        },
        ElRadioGroup: { template: '<div><slot /></div>' },
        ElRadioButton: {
          template:
            '<button type="button" :data-value="value" :disabled="disabled"><slot /></button>',
          props: ['value', 'disabled'],
        },
        ElButton: { template: '<button type="submit"><slot /></button>' },
        SearchThresholdControl: true,
      },
    },
  })
}

describe('RegulationsSearchForm', () => {
  it('emits trimmed query with selected params on submit', async () => {
    const wrapper = mountForm({ query: '', threshold: 0.6, orderBy: 'score' })

    await wrapper.find('input').setValue('  urlop dziekański  ')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('search')?.[0]).toEqual([
      { query: 'urlop dziekański', threshold: 0.6, orderBy: 'score' },
    ])
  })

  it('falls back to alphabetical order without a query', async () => {
    const wrapper = mountForm({ query: 'stypendium', threshold: 0.5, orderBy: 'score' })

    await wrapper.find('input').setValue('   ')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('search')?.[0]).toEqual([{ query: '', threshold: 0.5, orderBy: 'name' }])
  })

  it('disables ordering by relevance without a query', async () => {
    const wrapper = mountForm({ query: '', threshold: 0.5, orderBy: 'name' })

    const scoreButton = wrapper.find('button[data-value="score"]')
    expect(scoreButton.attributes('disabled')).toBeDefined()

    await wrapper.find('input').setValue('stypendium')

    expect(scoreButton.attributes('disabled')).toBeUndefined()
  })
})
