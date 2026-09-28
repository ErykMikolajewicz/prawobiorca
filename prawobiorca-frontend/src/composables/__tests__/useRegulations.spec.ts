import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getPublicRegulations } from '@/api/generated/endpoints/regulations/regulations'
import { useRegulations } from '@/composables/useRegulations'
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
    presentationName: `Regulacja ${id}`,
    regulationType: 'ACT',
    preparationStatus: 'PREPARED',
  }
}

describe('useRegulations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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

  it('removes a regulation and marks another as in progress', async () => {
    vi.mocked(getPublicRegulations).mockResolvedValueOnce([regulation('a'), regulation('b')])

    const { regulations, hasPending, fetch, remove, markAsInProgress } = useRegulations('public')
    await fetch()

    remove('a')
    markAsInProgress('b')

    expect(regulations.value).toEqual([{ ...regulation('b'), preparationStatus: 'IN_PROGRESS' }])
    expect(hasPending.value).toBe(true)
  })
})
