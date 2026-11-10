import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import SearchResultsList from '../SearchResultsList.vue'
import { createSearchResult } from '@/__tests__/factories'
import type { SearchResult } from '@/api/generated/model'

function mountList(
  results: Array<SearchResult>,
  props: { query?: string; canAddToCase?: boolean; selectedCaseId?: string } = {},
) {
  return mount(SearchResultsList, {
    props: { results, query: 'urlop', canAddToCase: true, selectedCaseId: 'case-1', ...props },
    global: { plugins: [ElementPlus] },
  })
}

function addButtons(wrapper: ReturnType<typeof mountList>) {
  return wrapper.findAll('button').filter((button) => button.text() === 'Dodaj do sprawy')
}

describe('SearchResultsList', () => {
  it('groups consecutive results of the same article under one header', () => {
    const wrapper = mountList([
      createSearchResult({ id: '1', header: 'Art. 1' }),
      createSearchResult({ id: '2', header: 'Art. 1' }),
      createSearchResult({ id: '3', header: 'Art. 2' }),
      createSearchResult({ id: '4', header: 'Art. 1' }),
    ])

    const groups = wrapper.findAll('.result-group')
    expect(groups.map((group) => group.find('.result-group-header').text())).toEqual([
      'Art. 1',
      'Art. 2',
      'Art. 1',
    ])
    expect(groups.map((group) => group.findAll('.el-card'))).toMatchObject([
      { length: 2 },
      { length: 1 },
      { length: 1 },
    ])
  })

  it('shows the text and the similarity of a result with its best fragment highlighted', () => {
    const wrapper = mountList([
      createSearchResult({
        score: 0.73456,
        elements: [
          { text: '1. Ustęp pierwszy', subsection: '1' },
          { text: '2. Ustęp drugi', subsection: '2' },
        ],
        highlight: { start_element: 1, end_element: 1 },
      }),
    ])

    const blocks = wrapper.findAll('.result-block')
    expect(blocks.map((block) => block.text())).toEqual(['1. Ustęp pierwszy', '2. Ustęp drugi'])
    expect(blocks.map((block) => block.classes('is-highlighted'))).toEqual([false, true])
    expect(wrapper.find('.score').text()).toBe('Podobieństwo: 0.735')
  })

  it('emits the added result together with the header of its group', async () => {
    const first = createSearchResult({ id: '1', header: 'Art. 1', text: 'Pierwszy' })
    const second = createSearchResult({
      id: '2',
      header: 'Art. 2',
      text: 'Drugi',
      highlight: { start_element: 0, end_element: 0 },
    })
    const wrapper = mountList([first, second])

    await addButtons(wrapper)[1]!.trigger('click')

    expect(wrapper.emitted('add-to-case')).toEqual([
      [
        {
          documentContent: 'Drugi',
          header: 'Art. 2',
          elements: second.elements,
          highlight: second.highlight,
        },
      ],
    ])
  })

  it('blocks adding a result until a case is selected', () => {
    const wrapper = mountList([createSearchResult()], { selectedCaseId: '' })

    expect(addButtons(wrapper)[0]!.attributes('disabled')).toBeDefined()
  })

  it('allows adding a result to the selected case', () => {
    const wrapper = mountList([createSearchResult()])

    expect(addButtons(wrapper)[0]!.attributes('disabled')).toBeUndefined()
  })

  it('does not offer adding results when the user cannot do it', () => {
    const wrapper = mountList([createSearchResult()], { canAddToCase: false })

    expect(addButtons(wrapper)).toHaveLength(0)
  })

  it('informs that the query has no results', () => {
    const wrapper = mountList([], { query: 'urlop' })

    expect(wrapper.text()).toBe('Brak wyników dla zapytania: "urlop"')
  })

  it('shows nothing before the first search', () => {
    const wrapper = mountList([], { query: '' })

    expect(wrapper.text()).toBe('')
  })
})
