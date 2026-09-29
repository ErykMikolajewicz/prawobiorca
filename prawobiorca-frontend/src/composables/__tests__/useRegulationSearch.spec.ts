import { describe, it, expect, vi, beforeEach } from 'vitest'
import { searchRegulationDocuments } from '@/api/generated/endpoints/regulations/regulations'
import { searchUserRegulationDocuments } from '@/api/generated/endpoints/user-regulations/user-regulations'
import { useRegulationSearch } from '@/composables/useRegulationSearch'
import type { SearchRegulationDocumentsParams, SearchResult } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  searchRegulationDocuments: vi.fn(),
}))

vi.mock('@/api/generated/endpoints/user-regulations/user-regulations', () => ({
  searchUserRegulationDocuments: vi.fn(),
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
    unit_type: null,
    unit_number: null,
    unit_path: null,
    elements: null,
    highlight: null,
  }
}

describe('useRegulationSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('searches the user regulation for user scope', async () => {
    vi.mocked(searchUserRegulationDocuments).mockResolvedValueOnce([result('a')])

    const { results, search } = useRegulationSearch('user', 'uuid-1')
    await search(params)

    expect(searchUserRegulationDocuments).toHaveBeenCalledWith('uuid-1', params)
    expect(searchRegulationDocuments).not.toHaveBeenCalled()
    expect(results.value).toEqual([result('a')])
  })

  it('ignores a response that arrives after a newer search', async () => {
    let resolveStale: ((value: Array<SearchResult>) => void) | undefined
    vi.mocked(searchRegulationDocuments)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockResolvedValueOnce([result('fresh')])

    const { results, isSearching, search } = useRegulationSearch('public', 'uuid-1')

    const staleSearch = search(params)
    await search({ ...params, order_by: 'score' })
    resolveStale?.([result('stale')])
    await staleSearch

    expect(results.value).toEqual([result('fresh')])
    expect(isSearching.value).toBe(false)
  })
})
