import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchResultItem from '../SearchResultItem.vue'
import type { SearchResultElement, SearchResultHighlight } from '@/api/generated/model'

function mountItem(
  result: string,
  elements?: Array<SearchResultElement> | null,
  selectedCaseId = 'case-1',
  highlight: SearchResultHighlight | null = null,
) {
  return mount(SearchResultItem, {
    props: { result, elements, score: 0.5, selectedCaseId, highlight, canAddToCase: true },
    global: {
      stubs: {
        ElCard: { template: '<div class="el-card"><slot /></div>' },
        ElTooltip: { template: '<div><slot /></div>' },
        ElButton: { template: '<button><slot /></button>' },
      },
    },
  })
}

describe('SearchResultItem', () => {
  it('falls back to the flat text when no elements are provided', () => {
    const wrapper = mountItem('1. Ustęp pierwszy\n2. Ustęp drugi', null)

    expect(wrapper.find('.result-blocks').exists()).toBe(false)
    expect(wrapper.find('.result-plain').text()).toBe('1. Ustęp pierwszy\n2. Ustęp drugi')
  })

  it('groups elements sharing a subsection into one block', () => {
    const elements: Array<SearchResultElement> = [
      { text: '1. Ustęp pierwszy', subsection: '1' },
      { text: '1) punkt pierwszy', subsection: '1' },
      { text: '2. Ustęp drugi', subsection: '2' },
    ]

    const wrapper = mountItem('1. Ustęp pierwszy\n1) punkt pierwszy\n2. Ustęp drugi', elements)

    const blocks = wrapper.findAll('.result-block')
    expect(blocks).toHaveLength(2)
    expect(blocks[0]!.findAll('.result-line')).toHaveLength(2)
    expect(blocks[1]!.findAll('.result-line')).toHaveLength(1)
  })

  it('marks punkt/litera lines for extra indentation', () => {
    const elements: Array<SearchResultElement> = [
      { text: '1. Ustęp pierwszy', subsection: '1' },
      { text: '1) punkt pierwszy', subsection: '1' },
      { text: 'a) litera pierwsza', subsection: '1' },
    ]

    const wrapper = mountItem('irrelevant', elements)

    const lines = wrapper.findAll('.result-line')
    expect(lines[0]!.classes()).not.toContain('result-line--sub')
    expect(lines[1]!.classes()).toContain('result-line--sub')
    expect(lines[2]!.classes()).toContain('result-line--sub')
  })

  it('emits add-to-case with the flat text regardless of structured elements', async () => {
    const elements: Array<SearchResultElement> = [{ text: '1. Ustęp pierwszy', subsection: '1' }]
    const wrapper = mountItem('1. Ustęp pierwszy', elements)

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('add-to-case')?.[0]).toEqual([{ documentContent: '1. Ustęp pierwszy' }])
  })

  it('highlights blocks containing the best chunk span', () => {
    const elements: Array<SearchResultElement> = [
      { text: '1. Ustęp pierwszy', subsection: '1' },
      { text: '2. Ustęp drugi', subsection: '2' },
      { text: '3. Ustęp trzeci', subsection: '3' },
    ]
    const highlight = { start_element: 0, start_offset: 3, end_element: 1, end_offset: 8 }

    const wrapper = mountItem('irrelevant', elements, 'case-1', highlight)

    const blocks = wrapper.findAll('.result-block')
    expect(blocks[0]!.classes()).toContain('result-block--highlighted')
    expect(blocks[1]!.classes()).toContain('result-block--highlighted')
    expect(blocks[2]!.classes()).not.toContain('result-block--highlighted')
  })

  it('does not highlight anything without highlight', () => {
    const elements: Array<SearchResultElement> = [{ text: '1. Ustęp pierwszy', subsection: '1' }]

    const wrapper = mountItem('irrelevant', elements)

    expect(wrapper.find('.result-block--highlighted').exists()).toBe(false)
    expect(wrapper.find('.result-line').text()).toBe('1. Ustęp pierwszy')
  })
})
