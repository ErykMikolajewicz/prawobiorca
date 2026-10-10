import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { getPublicRegulations } from '@/api/generated/endpoints/regulations/regulations'
import { useRegulations } from '@/composables/useRegulations'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  getPublicRegulations: vi.fn(),
}))

vi.mock('@/api/generated/endpoints/user-regulations/user-regulations', () => ({
  getUserRegulations: vi.fn(),
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
    organizationId: null,
    suborganizationId: null,
  }
}

describe('useRegulations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('ignores a response that arrives after a newer request', async () => {
    let resolveStale: ((value: Array<RegulationRepresentation>) => void) | undefined
    vi.mocked(getPublicRegulations)
      .mockImplementationOnce(() => new Promise((resolve) => (resolveStale = resolve)))
      .mockResolvedValueOnce([regulation('fresh')])

    const { regulations, fetch } = useRegulations('public')

    const staleRequest = fetch()
    await fetch()
    resolveStale?.([regulation('stale')])
    await staleRequest

    expect(regulations.value.map((item) => item.id)).toEqual(['fresh'])
  })

  it('reports loading while regulations are being loaded', async () => {
    let resolveRequest: ((value: Array<RegulationRepresentation>) => void) | undefined
    vi.mocked(getPublicRegulations).mockImplementationOnce(
      () => new Promise((resolve) => (resolveRequest = resolve)),
    )

    const { isLoading, load } = useRegulations('public')

    const loading = load()
    expect(isLoading.value).toBe(true)

    resolveRequest?.([regulation('a')])
    await loading
    expect(isLoading.value).toBe(false)
  })

  it('removes a regulation and marks another as in progress', async () => {
    vi.mocked(getPublicRegulations).mockResolvedValueOnce([regulation('a'), regulation('b')])

    const { regulations, pendingIds, fetch, remove, markAsInProgress } = useRegulations('public')
    await fetch()

    remove('a')
    markAsInProgress('b')

    expect(regulations.value).toEqual([{ ...regulation('b'), preparationStatus: 'IN_PROGRESS' }])
    expect(pendingIds.value).toEqual(['b'])
  })

  it('replaces an updated regulation', async () => {
    vi.mocked(getPublicRegulations).mockResolvedValueOnce([regulation('a'), regulation('b')])

    const { regulations, fetch, update } = useRegulations('public')
    await fetch()

    update({ ...regulation('a'), presentationName: 'Nowa nazwa', description: 'Opis' })

    expect(regulations.value).toEqual([
      { ...regulation('a'), presentationName: 'Nowa nazwa', description: 'Opis' },
      regulation('b'),
    ])
  })

  it('filters public regulations by the selected organization', async () => {
    vi.mocked(getPublicRegulations).mockResolvedValue([])
    useOrganizationsStore().select('pwr', 'w10')

    const { fetch } = useRegulations('public')
    await fetch()

    expect(getPublicRegulations).toHaveBeenCalledWith({
      documentType: undefined,
      organizationId: 'pwr',
      suborganizationId: 'w10',
    })
  })

  it('reloads public regulations when the selected organization changes', async () => {
    vi.mocked(getPublicRegulations).mockResolvedValue([])

    useRegulations('public')
    useOrganizationsStore().select('pwr', '')
    await nextTick()

    expect(getPublicRegulations).toHaveBeenCalledWith({
      documentType: undefined,
      organizationId: 'pwr',
      suborganizationId: undefined,
    })
  })
})
