import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import RegulationCard from '../RegulationCard.vue'
import {
  confirmPublicRegulationUpload,
  retryPublicRegulationPreparation,
} from '@/api/generated/endpoints/regulations/regulations'
import type { RegulationPreparationStatus, RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  confirmPublicRegulationUpload: vi.fn(),
  retryPublicRegulationPreparation: vi.fn(),
}))

vi.mock('@/api/generated/endpoints/user-regulations/user-regulations', () => ({
  confirmUserRegulationUpload: vi.fn(),
  retryUserRegulationPreparation: vi.fn(),
}))

const RETRY_BUTTON = 'button[aria-label="Ponów przetwarzanie"]'
const OPTIONS_BUTTON = 'button[aria-label="Opcje regulacji"]'

function mountCard(preparationStatus: RegulationPreparationStatus, canManage: boolean) {
  const regulation: RegulationRepresentation = {
    id: 'uuid-1',
    createDate: '2026-09-29T10:00:00',
    presentationName: 'Ustawa testowa',
    description: null,
    regulationType: 'ACT',
    preparationStatus,
  }

  return mount(RegulationCard, {
    props: { regulation, target: 'public', canManage },
    global: {
      stubs: {
        RouterLink: {
          template: '<a class="router-link-stub"><slot /></a>',
        },
        ElCard: {
          template: '<div class="el-card"><slot /></div>',
        },
        RegulationTypeBadge: true,
        RegulationStatusBadge: {
          template: '<span class="status-badge-stub">{{ preparationStatus }}</span>',
          props: ['preparationStatus'],
        },
        IconMotion: true,
        RegulationDetailsDialog: {
          template:
            '<div v-if="modelValue" class="details-dialog-stub">' +
            '<button class="stub-update" @click="$emit(\'updated\', { ...regulation, presentationName: \'Nowa nazwa\' })" />' +
            '<button class="stub-delete" @click="$emit(\'deleted\', regulation.id)" />' +
            '</div>',
          props: ['modelValue', 'regulation', 'target', 'canManage'],
        },
      },
    },
  })
}

describe('RegulationCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search action and router-link when regulation is prepared', () => {
    const wrapper = mountCard('PREPARED', false)

    expect(wrapper.find('.router-link-stub').exists()).toBe(true)
    expect(wrapper.find('.status-badge-stub').exists()).toBe(false)
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it('renders status badge without retry action while preparation is in progress', () => {
    const wrapper = mountCard('IN_PROGRESS', true)

    expect(wrapper.find('.router-link-stub').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').text()).toBe('IN_PROGRESS')
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it('retries preparation when regulation failed and user can manage it', async () => {
    const wrapper = mountCard('FAILED', true)

    expect(wrapper.find('.status-badge-stub').text()).toBe('FAILED')
    const button = wrapper.find(RETRY_BUTTON)
    expect(button.exists()).toBe(true)

    vi.mocked(retryPublicRegulationPreparation).mockResolvedValueOnce(undefined)
    await button.trigger('click')

    expect(retryPublicRegulationPreparation).toHaveBeenCalledWith('uuid-1')
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
  })

  it('confirms the upload again when regulation was not started', async () => {
    const wrapper = mountCard('NOT_STARTED', true)

    vi.mocked(confirmPublicRegulationUpload).mockResolvedValueOnce(undefined)
    await wrapper.find(RETRY_BUTTON).trigger('click')

    expect(confirmPublicRegulationUpload).toHaveBeenCalledWith('uuid-1')
    expect(retryPublicRegulationPreparation).not.toHaveBeenCalled()
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
  })

  it('does not emit retry when the retry request fails', async () => {
    const wrapper = mountCard('FAILED', true)

    vi.mocked(retryPublicRegulationPreparation).mockRejectedValueOnce(new Error('boom'))
    await wrapper.find(RETRY_BUTTON).trigger('click')

    expect(wrapper.emitted('preparation-retried')).toBeUndefined()
  })

  it('does not render status, retry or search action when user cannot manage and not prepared', () => {
    const wrapper = mountCard('FAILED', false)

    expect(wrapper.find('.router-link-stub').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').exists()).toBe(false)
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it.each([true, false])(
    'opens details dialog from options button when canManage is %s',
    async (canManage) => {
      const wrapper = mountCard('PREPARED', canManage)

      expect(wrapper.find('.details-dialog-stub').exists()).toBe(false)

      await wrapper.find(OPTIONS_BUTTON).trigger('click')

      expect(wrapper.find('.details-dialog-stub').exists()).toBe(true)
    },
  )

  it('forwards update and delete events from details dialog', async () => {
    const wrapper = mountCard('PREPARED', true)

    await wrapper.find(OPTIONS_BUTTON).trigger('click')
    await wrapper.find('.stub-update').trigger('click')
    await wrapper.find('.stub-delete').trigger('click')

    expect(wrapper.emitted('updated')?.[0]?.[0]).toMatchObject({
      id: 'uuid-1',
      presentationName: 'Nowa nazwa',
    })
    expect(wrapper.emitted('deleted')?.[0]).toEqual(['uuid-1'])
  })
})
