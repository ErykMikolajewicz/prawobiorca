import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick, ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import {
  getRegulations,
  searchRegulations,
} from '@/api/generated/endpoints/regulations/regulations'
import { useRegulations } from '@/composables/useRegulations'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationsSearchParams } from '@/domain/regulations'
import type { RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  getRegulations: vi.fn(),
  searchRegulations: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

function regulation(id: string): RegulationRepresentation {
  return {
    id,
    createDate: '2026-09-29T10:00:00',
    presentationName: `Regulacja ${id}`,
    description: null,
    regulationType: 'ACT',
    preparationStatus: 'PREPARED',
    descriptionStatus: 'NOT_REQUESTED',
    organizationId: null,
    suborganizationId: null,
  }
}

const withoutQuery = (): RegulationsSearchParams => ({
  query: '',
  threshold: 0.5,
  orderBy: 'name',
})

describe('useRegulations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('ignores a response that arrives after a newer request', async () => {
    let resolveStale: ((value: Array<RegulationRepresentation>) => void) | undefined
    vi.mocked(getRegulations)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockResolvedValueOnce([regulation('fresh')])

    const { regulations, fetch } = useRegulations('PUBLIC', withoutQuery)

    const staleRequest = fetch()
    await fetch()
    resolveStale?.([regulation('stale')])
    await staleRequest

    expect(regulations.value.map((item) => item.id)).toEqual(['fresh'])
  })

  it('reports loading while regulations are being loaded', async () => {
    let resolveRequest: ((value: Array<RegulationRepresentation>) => void) | undefined
    vi.mocked(getRegulations).mockImplementationOnce(
      () => new Promise((resolve) => (resolveRequest = resolve)),
    )

    const { isLoading, load } = useRegulations('PUBLIC', withoutQuery)

    const loading = load()
    expect(isLoading.value).toBe(true)

    resolveRequest?.([regulation('a')])
    await loading
    expect(isLoading.value).toBe(false)
  })

  it('removes a regulation and marks another as in progress', async () => {
    vi.mocked(getRegulations).mockResolvedValueOnce([regulation('a'), regulation('b')])

    const { regulations, pendingIds, fetch, remove, markAsInProgress } = useRegulations(
      'PUBLIC',
      withoutQuery,
    )
    await fetch()

    remove('a')
    markAsInProgress('b')

    expect(regulations.value).toEqual([{ ...regulation('b'), preparationStatus: 'IN_PROGRESS' }])
    expect(pendingIds.value).toEqual(['b'])
  })

  it('treats a prepared regulation with description in progress as pending', async () => {
    vi.mocked(getRegulations).mockResolvedValueOnce([
      regulation('a'),
      { ...regulation('b'), preparationStatus: 'FAILED', descriptionStatus: 'IN_PROGRESS' },
    ])

    const { pendingIds, fetch, markDescriptionAsInProgress } = useRegulations(
      'PUBLIC',
      withoutQuery,
    )
    await fetch()

    markDescriptionAsInProgress('a')

    expect(pendingIds.value).toEqual(['a'])
  })

  it('replaces an updated regulation', async () => {
    vi.mocked(getRegulations).mockResolvedValueOnce([regulation('a'), regulation('b')])

    const { regulations, fetch, update } = useRegulations('PUBLIC', withoutQuery)
    await fetch()

    update({ ...regulation('a'), presentationName: 'Nowa nazwa', description: 'Opis' })

    expect(regulations.value).toEqual([
      { ...regulation('a'), presentationName: 'Nowa nazwa', description: 'Opis' },
      regulation('b'),
    ])
  })

  it('filters public regulations by the selected organization', async () => {
    vi.mocked(getRegulations).mockResolvedValue([])
    useOrganizationsStore().select('pwr', 'w10')

    const { fetch } = useRegulations('PUBLIC', withoutQuery)
    await fetch()

    expect(getRegulations).toHaveBeenCalledWith({
      scope: 'PUBLIC',
      documentType: undefined,
      organizationId: 'pwr',
      suborganizationId: 'w10',
    })
  })

  it('reloads public regulations when the selected organization changes', async () => {
    vi.mocked(getRegulations).mockResolvedValue([])

    useRegulations('PUBLIC', withoutQuery)
    useOrganizationsStore().select('pwr', '')
    await nextTick()

    expect(getRegulations).toHaveBeenCalledWith({
      scope: 'PUBLIC',
      documentType: undefined,
      organizationId: 'pwr',
      suborganizationId: undefined,
    })
  })

  it('sorts regulations alphabetically without a query', async () => {
    vi.mocked(getRegulations).mockResolvedValueOnce([
      { ...regulation('a'), presentationName: 'Statut' },
      { ...regulation('b'), presentationName: 'Ćwiczenia' },
      { ...regulation('c'), presentationName: 'Regulamin' },
    ])

    const { regulations, scores, fetch } = useRegulations('PUBLIC', withoutQuery)
    await fetch()

    expect(regulations.value.map((item) => item.presentationName)).toEqual([
      'Ćwiczenia',
      'Regulamin',
      'Statut',
    ])
    expect(scores.value).toEqual({})
    expect(searchRegulations).not.toHaveBeenCalled()
  })

  it('searches regulations by description when a query is given', async () => {
    vi.mocked(searchRegulations).mockResolvedValueOnce([
      { regulation: { ...regulation('a'), presentationName: 'Statut' }, score: 0.9 },
      { regulation: { ...regulation('b'), presentationName: 'Regulamin' }, score: 0.7 },
    ])
    const searchParams = ref<RegulationsSearchParams>({
      query: 'urlop dziekański',
      threshold: 0.6,
      orderBy: 'score',
    })

    const { regulations, scores, fetch } = useRegulations('PRIVATE', () => searchParams.value)
    await fetch()

    expect(searchRegulations).toHaveBeenCalledWith({
      scope: 'PRIVATE',
      documentType: undefined,
      query: 'urlop dziekański',
      threshold: 0.6,
    })
    expect(getRegulations).not.toHaveBeenCalled()
    expect(scores.value).toEqual({ a: 0.9, b: 0.7 })
    expect(regulations.value.map((item) => item.id)).toEqual(['a', 'b'])

    searchParams.value.orderBy = 'name'

    expect(regulations.value.map((item) => item.id)).toEqual(['b', 'a'])
  })

  it('hides a regulation without score while searching', async () => {
    vi.mocked(searchRegulations).mockResolvedValueOnce([
      { regulation: regulation('a'), score: 0.9 },
    ])

    const { regulations, fetch, add } = useRegulations('PUBLIC', () => ({
      query: 'stypendium',
      threshold: 0.5,
      orderBy: 'score',
    }))
    await fetch()

    add(regulation('b'))

    expect(regulations.value.map((item) => item.id)).toEqual(['a'])
  })
})
