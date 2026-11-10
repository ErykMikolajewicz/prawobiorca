import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ElMessage } from 'element-plus'
import { createHttpError } from '@/__tests__/factories'
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

  it('reports searching until the newest search finishes', async () => {
    let resolveStale: ((value: Array<SearchResult>) => void) | undefined
    let resolveNewest: ((value: Array<SearchResult>) => void) | undefined
    vi.mocked(searchRegulationDocuments)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockImplementationOnce(() => new Promise((resolve) => (resolveNewest = resolve)))

    const { isSearching, search } = useRegulationSearch('uuid-1')
    expect(isSearching.value).toBe(false)

    const staleSearch = search(params)
    const newestSearch = search({ ...params, order_by: 'score' })
    expect(isSearching.value).toBe(true)

    resolveStale?.([result('stale')])
    await staleSearch
    expect(isSearching.value).toBe(true)

    resolveNewest?.([result('fresh')])
    await newestSearch
    expect(isSearching.value).toBe(false)
  })

  it('shows an error and keeps the previous results when the search fails', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    vi.mocked(searchRegulationDocuments)
      .mockResolvedValueOnce([result('a')])
      .mockRejectedValueOnce(createHttpError(500))

    const { results, isSearching, search } = useRegulationSearch('uuid-1')
    await search(params)
    await search({ ...params, query: 'urlop' })

    expect(ElMessage.error).toHaveBeenCalledExactlyOnceWith(
      'Wystąpił błąd podczas przeszukiwania regulacji.',
    )
    expect(results.value).toEqual([result('a')])
    expect(isSearching.value).toBe(false)
  })

  it('does not report a failure of a search replaced by a newer one', async () => {
    let rejectStale: ((reason: Error) => void) | undefined
    vi.mocked(searchRegulationDocuments)
      .mockImplementationOnce(() => new Promise((_, reject) => (rejectStale = reject)))
      .mockResolvedValueOnce([result('fresh')])

    const { results, search } = useRegulationSearch('uuid-1')

    const staleSearch = search(params)
    await search({ ...params, order_by: 'score' })
    rejectStale?.(new Error('Service unavailable'))
    await staleSearch

    expect(ElMessage.error).not.toHaveBeenCalled()
    expect(results.value).toEqual([result('fresh')])
  })
})
