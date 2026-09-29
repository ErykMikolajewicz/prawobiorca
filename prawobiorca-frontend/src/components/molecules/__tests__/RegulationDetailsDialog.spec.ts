import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import RegulationDetailsDialog from '../RegulationDetailsDialog.vue'
import {
  deletePublicRegulation,
  getPublicRegulationDownloadUrl,
  updatePublicRegulation,
} from '@/api/generated/endpoints/regulations/regulations'
import type { RegulationPreparationStatus, RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  deletePublicRegulation: vi.fn(),
  getPublicRegulationDownloadUrl: vi.fn(),
  updatePublicRegulation: vi.fn(),
}))

vi.mock('@/api/generated/endpoints/user-regulations/user-regulations', () => ({
  deleteUserRegulation: vi.fn(),
  getUserRegulationDownloadUrl: vi.fn(),
  updateUserRegulation: vi.fn(),
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
): RegulationRepresentation {
  return {
    id: 'uuid-1',
    createDate: '2026-09-29T10:00:00',
    presentationName: 'Ustawa testowa',
    description: 'Opis ustawy',
    regulationType: 'ACT',
    preparationStatus,
  }
}

async function mountDialog(
  canManage: boolean,
  preparationStatus: RegulationPreparationStatus = 'PREPARED',
) {
  const wrapper = mount(RegulationDetailsDialog, {
    props: {
      modelValue: false,
      'onUpdate:modelValue': (value: boolean) => wrapper.setProps({ modelValue: value }),
      regulation: createRegulation(preparationStatus),
      target: 'public' as const,
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
            "<input :class=\"type === 'textarea' ? 'description-input' : 'name-input'\" :value=\"modelValue\" @input=\"$emit('update:modelValue', $event.target.value)\" />",
          props: ['modelValue', 'type'],
        },
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
  })

  it('saves edited name and description', async () => {
    const wrapper = await mountDialog(true)
    const updatedRegulation = {
      ...createRegulation('PREPARED'),
      presentationName: 'Nowa nazwa',
      description: 'Nowy opis',
    }
    vi.mocked(updatePublicRegulation).mockResolvedValueOnce(updatedRegulation)

    await wrapper.find('.name-input').setValue('Nowa nazwa')
    await wrapper.find('.description-input').setValue('Nowy opis')
    await findButton(wrapper, 'Zapisz')?.trigger('click')
    await flushPromises()

    expect(updatePublicRegulation).toHaveBeenCalledWith('uuid-1', {
      name: 'Nowa nazwa',
      description: 'Nowy opis',
    })
    expect(wrapper.emitted('updated')?.[0]).toEqual([updatedRegulation])
  })

  it('deletes regulation and closes dialog', async () => {
    const wrapper = await mountDialog(true)
    vi.mocked(deletePublicRegulation).mockResolvedValueOnce(undefined)

    await wrapper.find('.confirm-delete').trigger('click')
    await flushPromises()

    expect(deletePublicRegulation).toHaveBeenCalledWith('uuid-1')
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

  it('loads file preview into iframe', async () => {
    const wrapper = await mountDialog(false)
    vi.mocked(getPublicRegulationDownloadUrl).mockResolvedValueOnce(
      'https://storage.example.com/uuid-1',
    )

    await findButton(wrapper, 'Pokaż podgląd')?.trigger('click')
    await flushPromises()

    expect(getPublicRegulationDownloadUrl).toHaveBeenCalledWith('uuid-1')
    expect(wrapper.find('iframe').attributes('src')).toBe('https://storage.example.com/uuid-1')
  })

  it('does not offer preview when file upload was not confirmed', async () => {
    const wrapper = await mountDialog(true, 'NOT_STARTED')

    expect(findButton(wrapper, 'Pokaż podgląd')).toBeUndefined()
  })
})
