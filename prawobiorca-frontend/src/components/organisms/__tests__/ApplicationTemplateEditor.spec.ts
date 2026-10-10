import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApplicationTemplateEditor from '../ApplicationTemplateEditor.vue'
import { updateApplicationTemplate } from '@/api/generated/endpoints/application-templates/application-templates'
import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/application-templates/application-templates', () => ({
  publishApplicationTemplate: vi.fn(),
  unpublishApplicationTemplate: vi.fn(),
  updateApplicationTemplate: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

function createTemplate(
  overrides: Partial<ApplicationTemplateRepresentation> = {},
): ApplicationTemplateRepresentation {
  return {
    id: 'template-1',
    createDate: '2026-10-11T10:00:00',
    name: 'Wniosek',
    status: 'DRAFT',
    fields: [],
    instructions: 'Instrukcje',
    organizationId: null,
    suborganizationId: null,
    ...overrides,
  }
}

function mountEditor(template: ApplicationTemplateRepresentation) {
  return mount(ApplicationTemplateEditor, {
    props: { template },
    global: {
      stubs: {
        MdEditor: true,
        ApplicationTemplateStatusBadge: true,
        ApplicationTemplateFieldEditor: true,
        ApplicationTemplatePreviewDialog: true,
      },
    },
  })
}

describe('ApplicationTemplateEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('saves organization and suborganization of the template', async () => {
    const template = createTemplate({ organizationId: 'pwr', suborganizationId: 'w10' })
    vi.mocked(updateApplicationTemplate).mockResolvedValue(template)

    const wrapper = mountEditor(template)
    await wrapper
      .findAll('el-button')
      .find((button) => button.text() === 'Zapisz')!
      .trigger('click')
    await flushPromises()

    expect(updateApplicationTemplate).toHaveBeenCalledWith('template-1', {
      name: 'Wniosek',
      instructions: 'Instrukcje',
      organizationId: 'pwr',
      suborganizationId: 'w10',
      fields: [],
    })
  })

  it('saves a general template without organization', async () => {
    const template = createTemplate()
    vi.mocked(updateApplicationTemplate).mockResolvedValue(template)

    const wrapper = mountEditor(template)
    await wrapper
      .findAll('el-button')
      .find((button) => button.text() === 'Zapisz')!
      .trigger('click')
    await flushPromises()

    expect(updateApplicationTemplate).toHaveBeenCalledWith(
      'template-1',
      expect.objectContaining({ organizationId: null, suborganizationId: null }),
    )
  })
})
