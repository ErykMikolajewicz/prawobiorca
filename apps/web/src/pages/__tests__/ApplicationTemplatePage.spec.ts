import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ApplicationTemplatePage from '../ApplicationTemplatePage.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton, shownMessages } from '@/__tests__/dom'
import { createApplicationTemplate, createHttpError } from '@/__tests__/factories'
import {
  getAdminApplicationTemplate,
  updateApplicationTemplate,
} from '@/api/generated/endpoints/application-templates/application-templates'

import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/application-templates/application-templates')

async function mountPage() {
  const { global } = await createTestApp('/admin/application-templates/template-1')
  const wrapper = mount(ApplicationTemplatePage, {
    global: {
      ...global,
      stubs: { ...global.stubs, MdEditorV3: true, ApplicationTemplatePreviewDialog: true },
    },
    attachTo: document.body,
  })
  await flushPromises()
  return wrapper
}

function nameInputValue(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  return (wrapper.find('.name-input input').element as HTMLInputElement).value
}

describe('ApplicationTemplatePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(getAdminApplicationTemplate).mockResolvedValue(createApplicationTemplate())
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows the template from the address in the editor', async () => {
    const wrapper = await mountPage()

    expect(getAdminApplicationTemplate).toHaveBeenCalledExactlyOnceWith('template-1')
    expect(nameInputValue(wrapper)).toBe('Wniosek o urlop dziekański')
  })

  it('does not claim the template is missing while it is being loaded', async () => {
    let finishLoading: ((template: ApplicationTemplateRepresentation) => void) | undefined
    vi.mocked(getAdminApplicationTemplate).mockReturnValue(
      new Promise((resolve) => (finishLoading = resolve)),
    )

    const wrapper = await mountPage()
    expect(wrapper.text()).not.toContain('Nie znaleziono szablonu.')

    finishLoading?.(createApplicationTemplate())
    await flushPromises()
    expect(wrapper.find('.template-editor').exists()).toBe(true)
  })

  it('reports a template that could not be loaded', async () => {
    vi.mocked(getAdminApplicationTemplate).mockRejectedValue(createHttpError(404))

    const wrapper = await mountPage()

    expect(shownMessages('error')).toEqual(['Nie udało się pobrać szablonu wniosku.'])
    expect(wrapper.text()).toContain('Nie znaleziono szablonu.')
    expect(wrapper.find('.template-editor').exists()).toBe(false)
  })

  it('shows the template returned after saving', async () => {
    vi.mocked(updateApplicationTemplate).mockResolvedValue(
      createApplicationTemplate({ name: 'Wniosek o urlop zdrowotny' }),
    )
    const wrapper = await mountPage()

    await findButton('Zapisz')!.trigger('click')
    await flushPromises()

    expect(nameInputValue(wrapper)).toBe('Wniosek o urlop zdrowotny')
  })

  it('refreshes the template until its description is generated', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
    vi.mocked(getAdminApplicationTemplate)
      .mockResolvedValueOnce(createApplicationTemplate({ descriptionStatus: 'IN_PROGRESS' }))
      .mockResolvedValue(
        createApplicationTemplate({
          descriptionStatus: 'GENERATED',
          description: 'Wniosek o urlop od zajęć.',
        }),
      )
    const wrapper = await mountPage()
    expect(wrapper.text()).toContain('Generowanie opisu')

    await vi.advanceTimersByTimeAsync(5000)
    await flushPromises()

    expect(wrapper.text()).not.toContain('Generowanie opisu')
    expect(wrapper.find('textarea').element.value).toBe('Wniosek o urlop od zajęć.')

    await vi.advanceTimersByTimeAsync(30_000)
    expect(getAdminApplicationTemplate).toHaveBeenCalledTimes(2)
  })

  it('keeps the template when a background refresh fails', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
    vi.mocked(getAdminApplicationTemplate)
      .mockResolvedValueOnce(createApplicationTemplate({ descriptionStatus: 'IN_PROGRESS' }))
      .mockRejectedValue(createHttpError(503))
    const wrapper = await mountPage()

    await vi.advanceTimersByTimeAsync(5000)
    await flushPromises()

    expect(wrapper.find('.template-editor').exists()).toBe(true)
    expect(shownMessages('error')).toEqual([])
  })
})
