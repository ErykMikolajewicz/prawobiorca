import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import RegulationDetailsDialog from '../RegulationDetailsDialog.vue'
import { createTestApp } from '@/__tests__/app'
import { confirmPopconfirm, findButton, page, shownMessages } from '@/__tests__/dom'
import { createFailingRequest, createHttpError, createRegulation } from '@/__tests__/factories'
import {
  deleteRegulation,
  getRegulationDownloadUrlById,
  regenerateRegulationDescription,
  updateRegulation,
} from '@/api/generated/endpoints/regulations/regulations'
import { useAuthStore } from '@/stores/auth'
import type { RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations')

const NAME_INPUT = 'input[placeholder="Nazwa regulacji"]'
const DESCRIPTION_INPUT = 'textarea'

const regulation = createRegulation({
  id: 'uuid-1',
  presentationName: 'Ustawa testowa',
  description: 'Opis ustawy',
})

type DialogOptions = {
  canManage: boolean
  isAdmin?: boolean
  regulation?: Partial<RegulationRepresentation>
}

async function mountDialog(options: DialogOptions) {
  const { global } = await createTestApp()
  useAuthStore().isAdmin = options.isAdmin ?? false
  const wrapper: VueWrapper = mount(RegulationDetailsDialog, {
    props: {
      modelValue: false,
      'onUpdate:modelValue': (modelValue: boolean) => wrapper.setProps({ modelValue }),
      regulation: { ...regulation, ...options.regulation },
      canManage: options.canManage,
    },
    global,
    attachTo: document.body,
  })
  await wrapper.setProps({ modelValue: true })
  return wrapper
}

function dialog() {
  return page().find('.el-dialog')
}

function isDialogOpen() {
  return dialog().exists() && dialog().isVisible()
}

function inputValue(selector: string) {
  return dialog().find<HTMLInputElement | HTMLTextAreaElement>(selector).element.value
}

async function clickButton(text: string) {
  await findButton(text)!.trigger('click')
  await flushPromises()
}

function mockPreviewWindow() {
  const previewWindow = { opener: window, location: { href: '' }, close: vi.fn() }
  const open = vi.spyOn(window, 'open').mockReturnValueOnce(previewWindow as unknown as Window)
  return { previewWindow, open }
}

describe('RegulationDetailsDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  describe('editing', () => {
    it('saves edited name and description', async () => {
      const wrapper = await mountDialog({ canManage: true })
      const updatedRegulation = {
        ...regulation,
        presentationName: 'Nowa nazwa',
        description: 'Nowy opis',
      }
      vi.mocked(updateRegulation).mockResolvedValueOnce(updatedRegulation)

      await dialog().find(NAME_INPUT).setValue('Nowa nazwa')
      await dialog().find(DESCRIPTION_INPUT).setValue('Nowy opis')
      await clickButton('Zapisz')

      expect(updateRegulation).toHaveBeenCalledExactlyOnceWith('uuid-1', {
        name: 'Nowa nazwa',
        description: 'Nowy opis',
      })
      expect(wrapper.emitted('updated')).toEqual([[updatedRegulation]])
      expect(shownMessages('success')).toEqual(['Regulacja została zaktualizowana'])
    })

    it('trims the name and sends an empty description as null', async () => {
      await mountDialog({ canManage: true })
      vi.mocked(updateRegulation).mockResolvedValueOnce(regulation)

      await dialog().find(NAME_INPUT).setValue('  Nowa nazwa ')
      await dialog().find(DESCRIPTION_INPUT).setValue('   ')
      await clickButton('Zapisz')

      expect(updateRegulation).toHaveBeenCalledExactlyOnceWith('uuid-1', {
        name: 'Nowa nazwa',
        description: null,
      })
    })

    it('does not save a regulation without a name', async () => {
      const wrapper = await mountDialog({ canManage: true })

      await dialog().find(NAME_INPUT).setValue('   ')
      await clickButton('Zapisz')

      expect(shownMessages('warning')).toEqual(['Podaj nazwę regulacji.'])
      expect(updateRegulation).not.toHaveBeenCalled()
      expect(wrapper.emitted('updated')).toBeUndefined()
    })

    it('reports a regulation that could not be saved', async () => {
      const wrapper = await mountDialog({ canManage: true })
      vi.mocked(updateRegulation).mockRejectedValueOnce(createHttpError(500))

      await clickButton('Zapisz')

      expect(shownMessages('error')).toEqual(['Nie udało się zaktualizować regulacji'])
      expect(shownMessages('success')).toEqual([])
      expect(wrapper.emitted('updated')).toBeUndefined()
    })

    it('shows the current data again after unsaved changes were abandoned', async () => {
      const wrapper = await mountDialog({ canManage: true })
      await dialog().find(NAME_INPUT).setValue('Porzucona nazwa')
      await dialog().find(DESCRIPTION_INPUT).setValue('Porzucony opis')

      await wrapper.setProps({ modelValue: false })
      await wrapper.setProps({ modelValue: true })

      expect(inputValue(NAME_INPUT)).toBe('Ustawa testowa')
      expect(inputValue(DESCRIPTION_INPUT)).toBe('Opis ustawy')
    })

    it('deletes regulation after confirmation and closes dialog', async () => {
      const wrapper = await mountDialog({ canManage: true })

      await clickButton('Usuń')
      expect(deleteRegulation).not.toHaveBeenCalled()
      await confirmPopconfirm()
      await flushPromises()

      expect(deleteRegulation).toHaveBeenCalledExactlyOnceWith('uuid-1')
      expect(wrapper.emitted('deleted')).toEqual([['uuid-1']])
      expect(shownMessages('success')).toEqual(['Regulacja została usunięta'])
      expect(isDialogOpen()).toBe(false)
    })

    it('keeps the dialog open and reports an error when deleting fails', async () => {
      const wrapper = await mountDialog({ canManage: true })
      vi.mocked(deleteRegulation).mockRejectedValueOnce(createHttpError(500))

      await clickButton('Usuń')
      await confirmPopconfirm()
      await flushPromises()

      expect(shownMessages('error')).toEqual(['Nie udało się usunąć regulacji'])
      expect(wrapper.emitted('deleted')).toBeUndefined()
      expect(isDialogOpen()).toBe(true)
    })
  })

  describe('running requests', () => {
    it.each([
      [
        'Zapisz',
        (request: Promise<never>) => vi.mocked(updateRegulation).mockReturnValueOnce(request),
      ],
      [
        'Wygeneruj opis przez AI',
        (request: Promise<never>) =>
          vi.mocked(regenerateRegulationDescription).mockReturnValueOnce(request),
      ],
    ])('shows "%s" as busy until its request ends', async (label, mockRequest) => {
      const { request, fail } = createFailingRequest()
      mockRequest(request)
      await mountDialog({ canManage: true, isAdmin: true })
      expect(findButton(label)!.classes()).not.toContain('is-loading')

      await clickButton(label)
      expect(findButton(label)!.classes()).toContain('is-loading')

      fail()
      await flushPromises()
      expect(findButton(label)!.classes()).not.toContain('is-loading')
    })

    it('shows loading the preview as busy until its request ends', async () => {
      const { request, fail } = createFailingRequest()
      vi.mocked(getRegulationDownloadUrlById).mockReturnValueOnce(request)
      mockPreviewWindow()
      await mountDialog({ canManage: false })
      expect(findButton('Pokaż podgląd')!.classes()).not.toContain('is-loading')

      await clickButton('Pokaż podgląd')
      expect(findButton('Pokaż podgląd')!.classes()).toContain('is-loading')

      fail()
      await flushPromises()
      expect(findButton('Pokaż podgląd')!.classes()).not.toContain('is-loading')
    })

    it('shows deleting as busy until its request ends', async () => {
      const { request, fail } = createFailingRequest()
      vi.mocked(deleteRegulation).mockReturnValueOnce(request)
      await mountDialog({ canManage: true })

      await clickButton('Usuń')
      await confirmPopconfirm()
      await flushPromises()
      expect(findButton('Usuń')!.classes()).toContain('is-loading')

      fail()
      await flushPromises()
      expect(findButton('Usuń')!.classes()).not.toContain('is-loading')
    })
  })

  describe('reading', () => {
    it('shows details read-only when user cannot manage regulation', async () => {
      await mountDialog({ canManage: false })

      expect(dialog().find(NAME_INPUT).exists()).toBe(false)
      expect(dialog().find(DESCRIPTION_INPUT).exists()).toBe(false)
      expect(findButton('Zapisz')).toBeUndefined()
      expect(findButton('Usuń')).toBeUndefined()
      expect(dialog().text()).toContain('Ustawa testowa')
      expect(dialog().find('.regulation-description').text()).toBe('Opis ustawy')
    })

    it('informs a reader that the regulation has no description', async () => {
      await mountDialog({ canManage: false, regulation: { description: null } })

      expect(dialog().find('.regulation-description').text()).toBe('Brak opisu')
    })

    it('shows when the regulation was added', async () => {
      await mountDialog({ canManage: false })

      expect(dialog().text()).toContain('29.09.2026, 10:00')
    })
  })

  describe('file preview', () => {
    it('opens file preview in new browser tab', async () => {
      await mountDialog({ canManage: false })
      const { previewWindow, open } = mockPreviewWindow()
      vi.mocked(getRegulationDownloadUrlById).mockResolvedValueOnce(
        'https://storage.example.com/uuid-1',
      )

      await clickButton('Pokaż podgląd')

      expect(open).toHaveBeenCalledExactlyOnceWith('', '_blank')
      expect(getRegulationDownloadUrlById).toHaveBeenCalledExactlyOnceWith('uuid-1')
      expect(previewWindow.opener).toBeNull()
      expect(previewWindow.location.href).toBe('https://storage.example.com/uuid-1')
    })

    it('closes the opened tab and reports an error when the preview cannot be loaded', async () => {
      await mountDialog({ canManage: false })
      const { previewWindow } = mockPreviewWindow()
      vi.mocked(getRegulationDownloadUrlById).mockRejectedValueOnce(createHttpError(404))

      await clickButton('Pokaż podgląd')

      expect(previewWindow.close).toHaveBeenCalledOnce()
      expect(previewWindow.location.href).toBe('')
      expect(shownMessages('error')).toEqual(['Nie udało się pobrać podglądu pliku'])
    })

    it('does not offer preview when file upload was not confirmed', async () => {
      await mountDialog({ canManage: true, regulation: { preparationStatus: 'NOT_STARTED' } })

      expect(findButton('Pokaż podgląd')).toBeUndefined()
    })

    it.each(['IN_PROGRESS', 'FAILED', 'PREPARED'] as const)(
      'offers preview of an uploaded file of a regulation with status %s',
      async (preparationStatus) => {
        await mountDialog({ canManage: false, regulation: { preparationStatus } })

        expect(findButton('Pokaż podgląd')).toBeDefined()
      },
    )
  })

  describe('description generation', () => {
    it('starts description generation as admin', async () => {
      const wrapper = await mountDialog({ canManage: true, isAdmin: true })

      await clickButton('Wygeneruj opis przez AI')

      expect(regenerateRegulationDescription).toHaveBeenCalledExactlyOnceWith('uuid-1')
      expect(wrapper.emitted('description-generation-started')).toEqual([['uuid-1']])
      expect(shownMessages('success')).toEqual(['Generowanie opisu zostało rozpoczęte'])
    })

    it('explains why description generation could not be started', async () => {
      const wrapper = await mountDialog({ canManage: true, isAdmin: true })
      vi.mocked(regenerateRegulationDescription).mockRejectedValueOnce(createHttpError(409))

      await clickButton('Wygeneruj opis przez AI')

      expect(shownMessages('error')).toEqual([
        'Opis jest już generowany lub regulacja nie jest jeszcze przetworzona.',
      ])
      expect(wrapper.emitted('description-generation-started')).toBeUndefined()
    })

    it('does not offer description generation to normal user', async () => {
      await mountDialog({ canManage: true })

      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
    })

    it('does not offer description generation for a regulation the admin cannot manage', async () => {
      await mountDialog({
        canManage: false,
        isAdmin: true,
        regulation: { descriptionStatus: 'FAILED' },
      })

      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
      expect(dialog().find('.el-tag').exists()).toBe(false)
    })

    it('does not offer description generation before regulation is prepared', async () => {
      await mountDialog({
        canManage: true,
        isAdmin: true,
        regulation: { preparationStatus: 'IN_PROGRESS' },
      })

      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
    })

    it('locks description while it is being generated', async () => {
      await mountDialog({
        canManage: true,
        isAdmin: true,
        regulation: { descriptionStatus: 'IN_PROGRESS' },
      })

      expect(dialog().find(DESCRIPTION_INPUT).attributes('disabled')).toBeDefined()
      expect(dialog().find('.el-tag').text()).toBe('Generowanie opisu')
      expect(findButton('Wygeneruj opis przez AI')).toBeUndefined()
    })

    it('informs that description generation failed and allows another attempt', async () => {
      await mountDialog({
        canManage: true,
        isAdmin: true,
        regulation: { descriptionStatus: 'FAILED' },
      })

      expect(dialog().find('.el-tag').text()).toBe('Błąd generowania opisu')
      expect(findButton('Wygeneruj opis przez AI')).toBeDefined()
      expect(dialog().find(DESCRIPTION_INPUT).attributes('disabled')).toBeUndefined()
    })

    it('shows generated description when regulation is refreshed', async () => {
      const wrapper = await mountDialog({
        canManage: true,
        regulation: { descriptionStatus: 'IN_PROGRESS' },
      })

      await wrapper.setProps({
        regulation: {
          ...regulation,
          descriptionStatus: 'GENERATED',
          description: 'Wygenerowany opis',
        },
      })

      expect(inputValue(DESCRIPTION_INPUT)).toBe('Wygenerowany opis')
    })
  })
})
