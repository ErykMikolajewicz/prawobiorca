import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { getCasesList } from '@/api/generated/endpoints/cases/cases'
import { useCasesStore } from '@/stores/cases'
import { showApiError } from '@/utils/error'

vi.mock('@/api/generated/endpoints/cases/cases', () => ({
  getCasesList: vi.fn(),
}))

vi.mock('@/utils/error', () => ({
  showApiError: vi.fn(),
}))

describe('cases store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('load sets the newest case as active when nothing is stored', async () => {
    vi.mocked(getCasesList).mockResolvedValueOnce([
      { id: '2', name: 'Nowsza' },
      { id: '1', name: 'Starsza' },
    ])
    const store = useCasesStore()

    await store.load()

    expect(store.activeCaseId).toBe('2')
  })

  it('load restores the stored active case', async () => {
    localStorage.setItem('active-case-id', '1')
    vi.mocked(getCasesList).mockResolvedValueOnce([
      { id: '2', name: 'Nowsza' },
      { id: '1', name: 'Starsza' },
    ])
    const store = useCasesStore()

    await store.load()

    expect(store.activeCaseId).toBe('1')
  })

  it('load ignores a stored case that is not on the list', async () => {
    localStorage.setItem('active-case-id', 'missing')
    vi.mocked(getCasesList).mockResolvedValueOnce([{ id: '1', name: 'Sprawa' }])
    const store = useCasesStore()

    await store.load()

    expect(store.activeCaseId).toBe('1')
  })

  it('add prepends the case and sets it as active', () => {
    const store = useCasesStore()
    store.add({ id: '1', name: 'Pierwsza' })

    store.add({ id: '2', name: 'Druga' })

    expect(store.cases).toEqual([
      { id: '2', name: 'Druga' },
      { id: '1', name: 'Pierwsza' },
    ])
    expect(store.activeCaseId).toBe('2')
  })

  it('remove of the active case activates the newest remaining case', () => {
    const store = useCasesStore()
    store.add({ id: '1', name: 'Pierwsza' })
    store.add({ id: '2', name: 'Druga' })
    store.add({ id: '3', name: 'Trzecia' })

    store.remove('3')

    expect(store.activeCaseId).toBe('2')
  })

  it('setActive stores the case id', () => {
    const store = useCasesStore()

    store.setActive('1')

    expect(store.activeCaseId).toBe('1')
    expect(localStorage.getItem('active-case-id')).toBe('1')
  })

  it('load stores fetched cases', async () => {
    vi.mocked(getCasesList).mockResolvedValueOnce([{ id: '1', name: 'Sprawa' }])
    const store = useCasesStore()

    await store.load()

    expect(store.cases).toEqual([{ id: '1', name: 'Sprawa' }])
  })

  it('load shows an error and keeps cases when the request fails', async () => {
    const error = new Error('Request failed')
    vi.mocked(getCasesList).mockRejectedValueOnce(error)
    const store = useCasesStore()
    store.add({ id: '1', name: 'Sprawa' })

    await store.load()

    expect(showApiError).toHaveBeenCalledWith(error, {
      defaultMessage: 'Nie udało się pobrać spraw.',
    })
    expect(store.cases).toEqual([{ id: '1', name: 'Sprawa' }])
  })

  it('remove deletes the case with the given id', () => {
    const store = useCasesStore()
    store.add({ id: '1', name: 'Pierwsza' })
    store.add({ id: '2', name: 'Druga' })

    store.remove('1')

    expect(store.cases).toEqual([{ id: '2', name: 'Druga' }])
  })
})
