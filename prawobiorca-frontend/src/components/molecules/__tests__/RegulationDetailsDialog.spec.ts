import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import RegulationDetailsDialog from '../RegulationDetailsDialog.vue'
import {
  deleteRegulation,
  getRegulationDownloadUrlById,
  regenerateRegulationDescription,
  updateRegulation,
} from '@/api/generated/endpoints/regulations/regulations'
import { useAuthStore } from '@/stores/auth'
import type {
  RegulationDescriptionStatus,
  RegulationPreparationStatus,
  RegulationRepresentation,
} from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  deleteRegulation: vi.fn(),
  getRegulationDownloadUrlById: vi.fn(),
  regenerateRegulationDescription: vi.fn(),
  updateRegulation: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}))

function createRegulation(
  preparationStatus: RegulationPreparationStatus,
  descriptionStatus: RegulationDescriptionStatus = 'NOT_REQUESTED',
): RegulationRepresentation {
  return {
    id: 'uuid-1',
    createDate: '2026-09-29T10:00:00',
    presentationName: 'Ustawa testowa',
    description: 'Opis ustawy',
    regulationType: 'ACT',
    preparationStatus,
    descriptionStatus,
    organizationId: null,
    suborganizationId: null,
  }
}

async function mountDialog(
  canManage: boolean,
  preparationStatus: RegulationPreparationStatus = 'PREPARED',
  descriptionStatus: RegulationDescriptionStatus = 'NOT_REQUESTED',
) {
  const wrapper = mount(RegulationDetailsDialog, {
    props: {
      modelValue: false,
      'onUpdate:modelValue': (value: boolean) => wrapper.setProps({ modelValue: value }),
      regulation: createRegulation(preparationStatus, descriptionStatus),
      canManage,
    },
    global: {
      stubs: {
        ElDialog: {
          template:
            '<div v-if="modelValue" class="dialog-stub"><slot /><slot name="footer" /></div>',
          props: ['modelValue'],
        },
        ElForm: { template: '<form><slot /></form>' },
        ElFormItem: { template: '<div><slot /></div>' },
        ElInput: {
          template:
            '<input :class="type === \'textarea\' ? \'description-input\' : \'name-input\'" :value="modelValue" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
          props: ['modelValue', 'type', 'disabled'],
        },
        ElTag: { template: '<span class="tag-stub"><slot /></span>' },
        ElButton: {
          template: '<button @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        ElPopconfirm: {
          template:
            '<div><slot name="reference" /><button class="confirm-delete" @click="$emit(\'confirm\')" /></div>',
        },
      },
    },
  })
  await wrapper.setProps({ modelValue: true })
  return wrapper
}

function findButton(wrapper: Awaited<ReturnType<typeof mountDialog>>, text: string) {
  return wrapper.findAll('button').find((button) => button.text() === text)
}

describe('RegulationDetailsDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('saves edited name and description', async () => {
    const wrapper = await mountDialog(true)
    const updatedRegulation = {
      ...createRegulation('PREPARED'),
      presentationName: 'Nowa nazwa',
      description: 'Nowy opis',
    }
    vi.mocked(updateRegulation).mockResolvedValueOnce(updatedRegulation)

    await wrapper.find('.name-input').setValue('Nowa nazwa')
    await wrapper.find('.description-input').setValue('Nowy opis')
    await findButton(wrapper, 'Zapisz')?.trigger('click')
    await flushPromises()

    expect(updateRegulation).toHaveBeenCalledWith('uuid-1', {
      name: 'Nowa nazwa',
      description: 'Nowy opis',
    })
    expect(wrapper.emitted('updated')?.[0]).toEqual([updatedRegulation])
  })

  it('deletes regulation and closes dialog', async () => {
    const wrapper = await mountDialog(true)
    vi.mocked(deleteRegulation).mockResolvedValueOnce(undefined)

    await wrapper.find('.confirm-delete').trigger('click')
    await flushPromises()

    expect(deleteRegulation).toHaveBeenCalledWith('uuid-1')
    expect(wrapper.emitted('deleted')?.[0]).toEqual(['uuid-1'])
    expect(wrapper.find('.dialog-stub').exists()).toBe(false)
  })

  it('shows details read-only when user cannot manage regulation', async () => {
    const wrapper = await mountDialog(false)

    expect(wrapper.find('.name-input').exists()).toBe(false)
    expect(wrapper.find('.confirm-delete').exists()).toBe(false)
    expect(findButton(wrapper, 'Zapisz')).toBeUndefined()
    expect(wrapper.text()).toContain('Ustawa testowa')
    expect(wrapper.text()).toContain('Opis ustawy')
  })

  it('opens file preview in new browser tab', async () => {
    const wrapper = await mountDialog(false)
    const previewWindow = { opener: window, location: { href: '' }, close: vi.fn() }
    const openSpy = vi.spyOn(window, 'open').mockReturnValueOnce(previewWindow as unknown as Window)
    vi.mocked(getRegulationDownloadUrlById).mockResolvedValueOnce(
      'https://storage.example.com/uuid-1',
    )

    await findButton(wrapper, 'Pokaż podgląd')?.trigger('click')
    await flushPromises()

    expect(openSpy).toHaveBeenCalledWith('', '_blank')
    expect(getRegulationDownloadUrlById).toHaveBeenCalledWith('uuid-1')
    expect(previewWindow.opener).toBeNull()
    expect(previewWindow.location.href).toBe('https://storage.example.com/uuid-1')
    openSpy.mockRestore()
  })

  it('starts description generation as admin', async () => {
    useAuthStore().isAdmin = true
    const wrapper = await mountDialog(true)
    vi.mocked(regenerateRegulationDescription).mockResolvedValueOnce(undefined)

    await findButton(wrapper, 'Wygeneruj opis przez AI')?.trigger('click')
    await flushPromises()

    expect(regenerateRegulationDescription).toHaveBeenCalledWith('uuid-1')
    expect(wrapper.emitted('description-generation-started')?.[0]).toEqual(['uuid-1'])
  })

  it('does not offer description generation to normal user', async () => {
    const wrapper = await mountDialog(true)

    expect(findButton(wrapper, 'Wygeneruj opis przez AI')).toBeUndefined()
  })

  it('does not offer description generation before regulation is prepared', async () => {
    useAuthStore().isAdmin = true
    const wrapper = await mountDialog(true, 'IN_PROGRESS')

    expect(findButton(wrapper, 'Wygeneruj opis przez AI')).toBeUndefined()
  })

  it('locks description while it is being generated', async () => {
    useAuthStore().isAdmin = true
    const wrapper = await mountDialog(true, 'PREPARED', 'IN_PROGRESS')

    expect(wrapper.find('.description-input').attributes('disabled')).toBeDefined()
    expect(wrapper.find('.tag-stub').text()).toBe('Generowanie opisu')
    expect(findButton(wrapper, 'Wygeneruj opis przez AI')).toBeUndefined()
  })

  it('shows generated description when regulation is refreshed', async () => {
    const wrapper = await mountDialog(true, 'PREPARED', 'IN_PROGRESS')

    await wrapper.setProps({
      regulation: {
        ...createRegulation('PREPARED', 'GENERATED'),
        description: 'Wygenerowany opis',
      },
    })

    expect((wrapper.find('.description-input').element as HTMLInputElement).value).toBe(
      'Wygenerowany opis',
    )
  })

  it('does not offer preview when file upload was not confirmed', async () => {
    const wrapper = await mountDialog(true, 'NOT_STARTED')

    expect(findButton(wrapper, 'Pokaż podgląd')).toBeUndefined()
  })
})
