import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchResultsList from '../SearchResultsList.vue'
import type { SearchResult } from '@/api/generated/model'

const mockResults: SearchResult[] = [
  {
    id: '1',
    score: 0.5,
    text: 'Ustęp pierwszy',
    header: 'Art. 1',
    unit_type: null,
    unit_number: null,
    unit_path: null,
    elements: [{ text: 'Ustęp pierwszy', subsection: null }],
    highlight: { start_element: 0, start_offset: 0, end_element: 0, end_offset: 5 },
  },
]

function mountList() {
  return mount(SearchResultsList, {
    props: { results: mockResults, query: 'ustęp', canAddToCase: true },
    global: {
      stubs: {
        SearchResultItem: {
          template: '<div class="stub-item">{{ highlight ? "highlighted" : "plain" }}</div>',
          props: ['highlight'],
        },
      },
    },
  })
}

describe('SearchResultsList', () => {
  it('passes highlight to results', () => {
    const wrapper = mountList()

    expect(wrapper.find('.stub-item').text()).toBe('highlighted')
  })
})
