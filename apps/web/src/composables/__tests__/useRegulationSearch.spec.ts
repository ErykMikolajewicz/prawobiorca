import { describe, it, expect, vi, beforeEach } from 'vitest'
import { searchRegulationDocuments } from '@/api/generated/endpoints/regulations/regulations'
import { useRegulationSearch } from '@/composables/useRegulationSearch'
import type { SearchRegulationDocumentsParams, SearchResult } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  searchRegulationDocuments: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

const params: SearchRegulationDocumentsParams = {
  query: 'stypendium',
  threshold: 0.2,
  order_by: 'document',
}

function result(id: string): SearchResult {
  return {
    id,
    score: 0.5,
    header: null,
    text: `Tekst ${id}`,
    elements: [],
    highlight: null,
  }
}

describe('useRegulationSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('searches the regulation documents', async () => {
    vi.mocked(searchRegulationDocuments).mockResolvedValueOnce([result('a')])

    const { results, search } = useRegulationSearch('uuid-1')
    await search(params)

    expect(searchRegulationDocuments).toHaveBeenCalledWith('uuid-1', params)
    expect(results.value).toEqual([result('a')])
  })

  it('ignores a response that arrives after a newer search', async () => {
    let resolveStale: ((value: Array<SearchResult>) => void) | undefined
    vi.mocked(searchRegulationDocuments)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockResolvedValueOnce([result('fresh')])

    const { results, isSearching, search } = useRegulationSearch('uuid-1')

    const staleSearch = search(params)
    await search({ ...params, order_by: 'score' })
    resolveStale?.([result('stale')])
    await staleSearch

    expect(results.value).toEqual([result('fresh')])
    expect(isSearching.value).toBe(false)
  })
})
