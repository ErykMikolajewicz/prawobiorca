import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import CasePage from '../CasePage.vue'
import { getPublishedApplicationTemplates } from '@/api/generated/endpoints/application-templates/application-templates'
import { useOrganizationsStore } from '@/stores/organizations'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: 'case-1' } }),
}))

vi.mock('@/api/generated/endpoints/cases/cases', () => ({
  deleteApplication: vi.fn(),
  deleteCaseDocument: vi.fn(),
  generateApplication: vi.fn(),
  getCaseApplications: vi.fn().mockResolvedValue([]),
  getCaseDocuments: vi.fn().mockResolvedValue([]),
}))

vi.mock('@/api/generated/endpoints/application-templates/application-templates', () => ({
  getPublishedApplicationTemplates: vi.fn(),
  searchPublishedApplicationTemplates: vi.fn(),
}))

vi.mock('@/composables/usePendingPolling', () => ({
  usePendingPolling: vi.fn(),
}))

function mountPage() {
  return mount(CasePage, {
    global: {
      stubs: {
        AppLayout: { template: '<div><slot /></div>' },
        GeneratePdfForm: true,
        PinnedDocumentsList: true,
        GeneratedApplicationsList: true,
        ElRow: { template: '<div><slot /></div>' },
        ElCol: { template: '<div><slot /></div>' },
      },
    },
  })
}

describe('CasePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    vi.mocked(getPublishedApplicationTemplates).mockResolvedValue([])
  })

  it('loads templates filtered by the selected organization', async () => {
    useOrganizationsStore().select('pwr', 'w10')

    mountPage()
    await flushPromises()

    expect(getPublishedApplicationTemplates).toHaveBeenCalledWith({
      organizationId: 'pwr',
      suborganizationId: 'w10',
    })
  })

  it('reloads templates when the selected organization changes', async () => {
    mountPage()
    await flushPromises()

    useOrganizationsStore().select('pwr', '')
    await flushPromises()

    expect(getPublishedApplicationTemplates).toHaveBeenLastCalledWith({
      organizationId: 'pwr',
      suborganizationId: undefined,
    })
  })
})
