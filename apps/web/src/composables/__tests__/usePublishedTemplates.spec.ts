import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'
import {
  getPublishedApplicationTemplates,
  searchPublishedApplicationTemplates,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { usePublishedTemplates } from '@/composables/usePublishedTemplates'
import { useOrganizationsStore } from '@/stores/organizations'
import type { PublishedApplicationTemplate } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/application-templates/application-templates', () => ({
  getPublishedApplicationTemplates: vi.fn(),
  searchPublishedApplicationTemplates: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

function template(id: string): PublishedApplicationTemplate {
  return { id, name: `Wniosek ${id}`, description: null, fields: [] }
}

describe('usePublishedTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    vi.mocked(getPublishedApplicationTemplates).mockResolvedValue([template('a'), template('b')])
  })

  it('does not search without a query', async () => {
    const { templates, searchResults, load } = usePublishedTemplates()

    await load()

    expect(templates.value).toEqual([template('a'), template('b')])
    expect(searchResults.value).toBeNull()
    expect(searchPublishedApplicationTemplates).not.toHaveBeenCalled()
  })

  it('searches templates filtered by the selected organization', async () => {
    useOrganizationsStore().select('pwr', 'w10')
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([template('b')])

    const { searchResults, search } = usePublishedTemplates()

    await search('urlop ')

    expect(searchPublishedApplicationTemplates).toHaveBeenCalledWith({
      organizationId: 'pwr',
      suborganizationId: 'w10',
      query: 'urlop ',
      aiAssisted: false,
    })
    expect(searchResults.value).toEqual([template('b')])
  })

  it('clears search results for a blank query', async () => {
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([template('b')])

    const { searchResults, search } = usePublishedTemplates()

    await search('urlop')
    await search('  ')

    expect(searchResults.value).toBeNull()
    expect(searchPublishedApplicationTemplates).toHaveBeenCalledTimes(1)
  })

  it('repeats the search with AI assistance when it is enabled', async () => {
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([template('a')])

    const { aiAssisted, search } = usePublishedTemplates()
    await search('urlop dziekański')

    aiAssisted.value = true
    await flushPromises()

    expect(searchPublishedApplicationTemplates).toHaveBeenLastCalledWith({
      organizationId: undefined,
      suborganizationId: undefined,
      query: 'urlop dziekański',
      aiAssisted: true,
    })
  })

  it('repeats the search when the selected organization changes', async () => {
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([template('a')])

    const { search } = usePublishedTemplates()
    await search('urlop')

    useOrganizationsStore().select('pwr', '')
    await flushPromises()

    expect(searchPublishedApplicationTemplates).toHaveBeenLastCalledWith({
      organizationId: 'pwr',
      suborganizationId: undefined,
      query: 'urlop',
      aiAssisted: false,
    })
  })

  it('ignores a search response that arrives after a newer search', async () => {
    let resolveStale: ((value: Array<PublishedApplicationTemplate>) => void) | undefined
    vi.mocked(searchPublishedApplicationTemplates)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockResolvedValueOnce([template('b')])

    const { searchResults, search } = usePublishedTemplates()

    const staleSearch = search('stary')
    await search('nowy')
    resolveStale!([template('a')])
    await staleSearch

    expect(searchResults.value).toEqual([template('b')])
  })

  it('marks searching until the newest search finishes', async () => {
    let resolveStale: ((value: Array<PublishedApplicationTemplate>) => void) | undefined
    let resolveNewest: ((value: Array<PublishedApplicationTemplate>) => void) | undefined
    vi.mocked(searchPublishedApplicationTemplates)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockImplementationOnce(() => new Promise((resolve) => (resolveNewest = resolve)))

    const { isSearching, search } = usePublishedTemplates()

    const staleSearch = search('stary')
    const newestSearch = search('nowy')
    expect(isSearching.value).toBe(true)

    resolveStale!([template('a')])
    await staleSearch
    expect(isSearching.value).toBe(true)

    resolveNewest!([template('b')])
    await newestSearch
    expect(isSearching.value).toBe(false)
  })

  it('stops searching when the query is cleared during a search', async () => {
    let resolveSearch: ((value: Array<PublishedApplicationTemplate>) => void) | undefined
    vi.mocked(searchPublishedApplicationTemplates).mockImplementationOnce(
      () => new Promise((resolve) => (resolveSearch = resolve)),
    )

    const { isSearching, searchResults, search } = usePublishedTemplates()

    const pendingSearch = search('urlop')
    await search('')
    expect(isSearching.value).toBe(false)

    resolveSearch!([template('a')])
    await pendingSearch
    expect(isSearching.value).toBe(false)
    expect(searchResults.value).toBeNull()
  })

  it('falls back to all templates and reports an error once when the newest search fails', async () => {
    let rejectStale: ((reason: Error) => void) | undefined
    vi.mocked(searchPublishedApplicationTemplates)
      .mockResolvedValueOnce([])
      .mockImplementationOnce(() => new Promise((_, reject) => (rejectStale = reject)))
      .mockRejectedValueOnce(new Error('Service unavailable'))

    const { isSearching, searchResults, search } = usePublishedTemplates()

    await search('Zmiana')
    expect(searchResults.value).toEqual([])

    const staleSearch = search('Zmiana w')
    await search('Zmiana wy')
    rejectStale!(new Error('Service unavailable'))
    await staleSearch

    expect(searchResults.value).toBeNull()
    expect(isSearching.value).toBe(false)
    expect(ElMessage.error).toHaveBeenCalledTimes(1)
  })
})
