import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchResultsList from '../SearchResultsList.vue'
import type { searchResult } from '@/types/api/search'

const mockResults: searchResult[] = [
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
    props: { results: mockResults, query: 'ustęp' },
    global: {
      stubs: {
        ElSwitch: {
          template:
            '<button class="el-switch" @click="$emit(\'update:modelValue\', !modelValue)" />',
          props: ['modelValue'],
        },
        SearchResultItem: {
          template: '<div class="stub-item">{{ highlight ? "highlighted" : "plain" }}</div>',
          props: ['highlight'],
        },
      },
    },
  })
}

describe('SearchResultsList', () => {
  it('passes highlight to results by default', () => {
    const wrapper = mountList()

    expect(wrapper.find('.stub-item').text()).toBe('highlighted')
  })

  it('does not pass highlight when switch is turned off', async () => {
    const wrapper = mountList()

    await wrapper.find('.el-switch').trigger('click')

    expect(wrapper.find('.stub-item').text()).toBe('plain')
  })
})
