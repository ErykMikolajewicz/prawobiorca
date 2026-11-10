import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import RegulationsSearchForm from '../RegulationsSearchForm.vue'
import { findOption } from '@/__tests__/dom'
import type { RegulationsSearchParams } from '@/domain/regulations'

const QUERY_INPUT = 'input[placeholder^="Opisz sprawę"]'
const ORDER_BY_SCORE = 'input[type="radio"][value="score"]'

function mountForm(searchParams: RegulationsSearchParams, canUseAdvancedThreshold = false) {
  return mount(RegulationsSearchForm, {
    props: { searchParams, canUseAdvancedThreshold },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

describe('RegulationsSearchForm', () => {
  it('emits trimmed query with selected params on submit', async () => {
    const wrapper = mountForm({ query: '', threshold: 0.6, orderBy: 'score' })

    await wrapper.find(QUERY_INPUT).setValue('  urlop dziekański  ')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('search')?.[0]).toEqual([
      { query: 'urlop dziekański', threshold: 0.6, orderBy: 'score' },
    ])
  })

  it('emits the relevance level chosen from presets', async () => {
    const wrapper = mountForm({ query: 'stypendium', threshold: 0.5, orderBy: 'name' })

    await findOption('Ścisły')!.trigger('click')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('search')?.[0]).toEqual([
      { query: 'stypendium', threshold: 0.7, orderBy: 'name' },
    ])
  })

  it('falls back to alphabetical order without a query', async () => {
    const wrapper = mountForm({ query: 'stypendium', threshold: 0.5, orderBy: 'score' })

    await wrapper.find(QUERY_INPUT).setValue('   ')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('search')?.[0]).toEqual([{ query: '', threshold: 0.5, orderBy: 'name' }])
  })

  it('disables ordering by relevance without a query', async () => {
    const wrapper = mountForm({ query: '', threshold: 0.5, orderBy: 'name' })

    expect(wrapper.find(ORDER_BY_SCORE).attributes('disabled')).toBeDefined()

    await wrapper.find(QUERY_INPUT).setValue('stypendium')

    expect(wrapper.find(ORDER_BY_SCORE).attributes('disabled')).toBeUndefined()
  })

  it('searches right after the order is changed', async () => {
    const wrapper = mountForm({ query: 'stypendium', threshold: 0.5, orderBy: 'name' })

    await wrapper.find(ORDER_BY_SCORE).setValue(true)

    expect(wrapper.emitted('search')).toEqual([
      [{ query: 'stypendium', threshold: 0.5, orderBy: 'score' }],
    ])
  })

  it('offers the advanced relevance level only when it is allowed', () => {
    expect(mountForm({ query: '', threshold: 0.5, orderBy: 'name' }).text()).not.toContain(
      'Zaawansowane',
    )
    expect(mountForm({ query: '', threshold: 0.5, orderBy: 'name' }, true).text()).toContain(
      'Zaawansowane',
    )
  })
})
