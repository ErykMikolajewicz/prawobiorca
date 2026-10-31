import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import {
  getPublishedApplicationTemplates,
  searchPublishedApplicationTemplates,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { usePublishedTemplates } from '@/composables/usePublishedTemplates'
import { defaultThreshold } from '@/domain/search'
import { useOrganizationsStore } from '@/stores/organizations'
import type {
  PublishedApplicationTemplate,
  PublishedApplicationTemplateSearchResult,
} from '@/api/generated/model'

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

function result(id: string, score: number): PublishedApplicationTemplateSearchResult {
  return { template: template(id), score }
}

describe('usePublishedTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    vi.mocked(getPublishedApplicationTemplates).mockResolvedValue([template('a'), template('b')])
  })

  it('does not search without a query', async () => {
    const { templates, scores, load } = usePublishedTemplates()

    await load()

    expect(templates.value).toEqual([template('a'), template('b')])
    expect(scores.value).toBeNull()
    expect(searchPublishedApplicationTemplates).not.toHaveBeenCalled()
  })

  it('searches templates filtered by the selected organization', async () => {
    useOrganizationsStore().select('pwr', 'w10')
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([result('b', 0.7)])

    const { scores, search } = usePublishedTemplates()

    await search('urlop')

    expect(searchPublishedApplicationTemplates).toHaveBeenCalledWith({
      organizationId: 'pwr',
      suborganizationId: 'w10',
      query: 'urlop',
      threshold: defaultThreshold,
    })
    expect(scores.value).toEqual({ b: 0.7 })
  })

  it('marks searching until the response arrives', async () => {
    let resolveSearch:
      | ((value: Array<PublishedApplicationTemplateSearchResult>) => void)
      | undefined
    vi.mocked(searchPublishedApplicationTemplates).mockImplementationOnce(
      () => new Promise((resolve) => (resolveSearch = resolve)),
    )

    const { searching, search } = usePublishedTemplates()

    const pendingSearch = search('urlop')
    expect(searching.value).toBe(true)

    resolveSearch!([])
    await pendingSearch

    expect(searching.value).toBe(false)
  })

  it('clears scores for an empty query', async () => {
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([result('b', 0.7)])

    const { scores, search } = usePublishedTemplates()

    await search('urlop')
    await search('')

    expect(scores.value).toBeNull()
  })

  it('repeats the search when the selected organization changes', async () => {
    vi.mocked(searchPublishedApplicationTemplates).mockResolvedValue([result('a', 0.6)])

    const { search } = usePublishedTemplates()
    await search('urlop')

    useOrganizationsStore().select('pwr', '')
    await flushPromises()

    expect(searchPublishedApplicationTemplates).toHaveBeenLastCalledWith({
      organizationId: 'pwr',
      suborganizationId: undefined,
      query: 'urlop',
      threshold: defaultThreshold,
    })
  })

  it('ignores a search response that arrives after a newer search', async () => {
    let resolveStale: ((value: Array<PublishedApplicationTemplateSearchResult>) => void) | undefined
    vi.mocked(searchPublishedApplicationTemplates)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockResolvedValueOnce([result('b', 0.8)])

    const { scores, search } = usePublishedTemplates()

    const staleSearch = search('stary')
    await search('nowy')
    resolveStale!([result('a', 0.9)])
    await staleSearch

    expect(scores.value).toEqual({ b: 0.8 })
  })
})
