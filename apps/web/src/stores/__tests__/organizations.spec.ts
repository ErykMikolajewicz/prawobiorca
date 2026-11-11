import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { getOrganizations } from '@/api/generated/endpoints/organizations/organizations'
import { useAuthStore } from '@/stores/auth'
import { useOrganizationsStore } from '@/stores/organizations'
import { showApiError } from '@/utils/error'

vi.mock('@/api/generated/endpoints/organizations/organizations', () => ({
  getOrganizations: vi.fn(),
}))

vi.mock('@/utils/error', () => ({
  showApiError: vi.fn(),
}))

const organizations = [
  {
    id: 'pwr',
    name: 'Politechnika Wrocławska',
    shortName: 'PWr',
    suborganizations: [
      { id: 'w4', name: 'Wydział Informatyki' },
      { id: 'w10', name: 'Wydział Mechaniczny' },
    ],
  },
  { id: 'uwr', name: 'Uniwersytet Wrocławski', shortName: 'UWr', suborganizations: [] },
]

describe('organizations store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    useAuthStore().isUserLogged = true
  })

  it('load selects the first organization when nothing is stored', async () => {
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganizationId).toBe('pwr')
    expect(store.selectedSuborganizationId).toBe('')
  })

  it('load selects nothing for a guest when nothing is stored', async () => {
    useAuthStore().isUserLogged = false
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganizationId).toBe('')
  })

  it('load restores the stored selection of a non-first suborganization', async () => {
    localStorage.setItem(
      'selected-organization',
      JSON.stringify({ organizationId: 'pwr', suborganizationId: 'w10' }),
    )
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganization?.shortName).toBe('PWr')
    expect(store.selectedSuborganization?.name).toBe('Wydział Mechaniczny')
  })

  it('load keeps a stored empty selection', async () => {
    localStorage.setItem(
      'selected-organization',
      JSON.stringify({ organizationId: '', suborganizationId: '' }),
    )
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganizationId).toBe('')
  })

  it('load falls back to the first organization when the stored one is not on the list', async () => {
    localStorage.setItem(
      'selected-organization',
      JSON.stringify({ organizationId: 'missing', suborganizationId: 'w10' }),
    )
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganizationId).toBe('pwr')
    expect(store.selectedSuborganizationId).toBe('')
  })

  it('load drops a stored suborganization that does not belong to the stored organization', async () => {
    localStorage.setItem(
      'selected-organization',
      JSON.stringify({ organizationId: 'uwr', suborganizationId: 'w10' }),
    )
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganizationId).toBe('uwr')
    expect(store.selectedSuborganizationId).toBe('')
  })

  it('load falls back to the default selection when the stored one is corrupted', async () => {
    localStorage.setItem('selected-organization', '{not-json')
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()

    await store.load()

    expect(store.selectedOrganizationId).toBe('pwr')
    expect(store.selectedSuborganizationId).toBe('')
  })

  it('load clears a previously selected suborganization when nothing is stored', async () => {
    vi.mocked(getOrganizations).mockResolvedValueOnce(organizations)
    const store = useOrganizationsStore()
    store.select('pwr', 'w10')
    localStorage.clear()

    await store.load()

    expect(store.selectedSuborganizationId).toBe('')
  })

  it('selectedSuborganization is searched only in the selected organization', () => {
    const store = useOrganizationsStore()
    store.organizations = organizations

    store.select('uwr', 'w10')

    expect(store.selectedOrganization?.shortName).toBe('UWr')
    expect(store.selectedSuborganization).toBeUndefined()
  })

  it('select stores the selection', () => {
    const store = useOrganizationsStore()

    store.select('uwr', '')

    expect(store.selectedOrganizationId).toBe('uwr')
    expect(JSON.parse(localStorage.getItem('selected-organization') ?? '')).toEqual({
      organizationId: 'uwr',
      suborganizationId: '',
    })
  })

  it('load shows an error when the request fails', async () => {
    const error = new Error('Request failed')
    vi.mocked(getOrganizations).mockRejectedValueOnce(error)
    const store = useOrganizationsStore()

    await store.load()

    expect(showApiError).toHaveBeenCalledWith(error, {
      defaultMessage: 'Nie udało się pobrać organizacji.',
    })
  })
})
