import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ApplicationTemplateEditor from '../ApplicationTemplateEditor.vue'
import {
  getAdminApplicationTemplate,
  regenerateApplicationTemplateDescription,
  updateApplicationTemplate,
} from '@/api/generated/endpoints/application-templates/application-templates'
import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/application-templates/application-templates', () => ({
  getAdminApplicationTemplate: vi.fn(),
  regenerateApplicationTemplateDescription: vi.fn(),
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
    description: null,
    descriptionStatus: 'NOT_REQUESTED',
    organizationId: null,
    suborganizationId: null,
    ...overrides,
  }
}

function findButton(wrapper: ReturnType<typeof mountEditor>, text: string) {
  return wrapper.findAll('el-button').find((button) => button.text() === text)
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
      description: null,
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

  it('saves the template before starting description generation', async () => {
    const template = createTemplate({ description: 'Wniosek o urlop.' })
    const generatingTemplate = createTemplate({ descriptionStatus: 'IN_PROGRESS' })
    vi.mocked(updateApplicationTemplate).mockResolvedValue(template)
    vi.mocked(getAdminApplicationTemplate).mockResolvedValue(generatingTemplate)

    const wrapper = mountEditor(template)
    await findButton(wrapper, 'Wygeneruj opis przez AI')!.trigger('click')
    await flushPromises()

    expect(updateApplicationTemplate).toHaveBeenCalledWith(
      'template-1',
      expect.objectContaining({ description: 'Wniosek o urlop.' }),
    )
    expect(regenerateApplicationTemplateDescription).toHaveBeenCalledWith('template-1')
    expect(wrapper.emitted('updated')).toEqual([[template], [generatingTemplate]])
  })

  it('does not start description generation when saving fails', async () => {
    vi.mocked(updateApplicationTemplate).mockRejectedValue(new Error('Invalid'))

    const wrapper = mountEditor(createTemplate())
    await findButton(wrapper, 'Wygeneruj opis przez AI')!.trigger('click')
    await flushPromises()

    expect(regenerateApplicationTemplateDescription).not.toHaveBeenCalled()
  })

  it('blocks editing while description is generated', () => {
    const wrapper = mountEditor(createTemplate({ descriptionStatus: 'IN_PROGRESS' }))

    expect(findButton(wrapper, 'Wygeneruj opis przez AI')).toBeUndefined()
    expect(findButton(wrapper, 'Zapisz')!.attributes('disabled')).toBe('true')
    expect(wrapper.find('el-form').attributes('disabled')).toBe('true')
    expect(wrapper.text()).toContain('Generowanie opisu')
  })
})
