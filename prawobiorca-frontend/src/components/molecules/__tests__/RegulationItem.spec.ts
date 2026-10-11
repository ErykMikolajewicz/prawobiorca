import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import RegulationItem from '../RegulationItem.vue'
import {
  confirmPublicRegulationUpload,
  retryPublicRegulationPreparation,
} from '@/api/generated/endpoints/regulations/regulations'
import { useOrganizationsStore } from '@/stores/organizations'
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

function mountItem(
  preparationStatus: RegulationPreparationStatus,
  canManage: boolean,
  overrides: Partial<RegulationRepresentation> = {},
) {
  const regulation: RegulationRepresentation = {
    id: 'uuid-1',
    createDate: '2026-09-29T10:00:00',
    presentationName: 'Ustawa testowa',
    description: null,
    regulationType: 'ACT',
    preparationStatus,
    organizationId: null,
    suborganizationId: null,
    ...overrides,
  }

  return mount(RegulationItem, {
    props: { regulation, target: 'public', canManage },
    global: {
      stubs: {
        RouterLink: {
          template: '<a class="router-link-stub"><slot /></a>',
        },
        RegulationTypeBadge: true,
        RegulationStatusBadge: {
          template: '<span class="status-badge-stub">{{ preparationStatus }}</span>',
          props: ['preparationStatus'],
        },
        IconMotion: true,
      },
    },
  })
}

describe('RegulationItem', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders organization and suborganization of the regulation', () => {
    useOrganizationsStore().organizations = [
      {
        id: 'pwr',
        name: 'Politechnika Wrocławska',
        shortName: 'PWr',
        suborganizations: [{ id: 'w10', name: 'Wydział Mechaniczny' }],
      },
    ]

    const wrapper = mountItem('PREPARED', false, {
      organizationId: 'pwr',
      suborganizationId: 'w10',
    })

    expect(wrapper.find('.regulation-organization').text()).toBe('PWr · Wydział Mechaniczny')
  })

  it('does not render organization for a general regulation', () => {
    const wrapper = mountItem('PREPARED', false)

    expect(wrapper.find('.regulation-organization').exists()).toBe(false)
  })

  it('renders search action and router-link when regulation is prepared', () => {
    const wrapper = mountItem('PREPARED', false)

    expect(wrapper.find('.router-link-stub').exists()).toBe(true)
    expect(wrapper.find('.status-badge-stub').exists()).toBe(false)
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it('renders status badge without retry action while preparation is in progress', () => {
    const wrapper = mountItem('IN_PROGRESS', true)

    expect(wrapper.find('.router-link-stub').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').text()).toBe('IN_PROGRESS')
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it('retries preparation when regulation failed and user can manage it', async () => {
    const wrapper = mountItem('FAILED', true)

    expect(wrapper.find('.status-badge-stub').text()).toBe('FAILED')
    const button = wrapper.find(RETRY_BUTTON)
    expect(button.exists()).toBe(true)

    vi.mocked(retryPublicRegulationPreparation).mockResolvedValueOnce(undefined)
    await button.trigger('click')

    expect(retryPublicRegulationPreparation).toHaveBeenCalledWith('uuid-1')
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
  })

  it('confirms the upload again when regulation was not started', async () => {
    const wrapper = mountItem('NOT_STARTED', true)

    vi.mocked(confirmPublicRegulationUpload).mockResolvedValueOnce(undefined)
    await wrapper.find(RETRY_BUTTON).trigger('click')

    expect(confirmPublicRegulationUpload).toHaveBeenCalledWith('uuid-1')
    expect(retryPublicRegulationPreparation).not.toHaveBeenCalled()
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
  })

  it('does not emit retry when the retry request fails', async () => {
    const wrapper = mountItem('FAILED', true)

    vi.mocked(retryPublicRegulationPreparation).mockRejectedValueOnce(new Error('boom'))
    await wrapper.find(RETRY_BUTTON).trigger('click')

    expect(wrapper.emitted('preparation-retried')).toBeUndefined()
  })

  it('does not render status, retry or search action when user cannot manage and not prepared', () => {
    const wrapper = mountItem('FAILED', false)

    expect(wrapper.find('.router-link-stub').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').exists()).toBe(false)
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it.each([true, false])(
    'emits open-details from options button when canManage is %s',
    async (canManage) => {
      const wrapper = mountItem('PREPARED', canManage)

      await wrapper.find(OPTIONS_BUTTON).trigger('click')

      expect(wrapper.emitted('open-details')?.[0]).toEqual(['uuid-1'])
    },
  )
})
