import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import RegulationItem from '../RegulationItem.vue'
import { shownMessages } from '@/__tests__/dom'
import { createHttpError } from '@/__tests__/factories'
import {
  confirmRegulationUpload,
  retryRegulationPreparation,
} from '@/api/generated/endpoints/regulations/regulations'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationScope } from '@/domain/regulations'
import type { RegulationPreparationStatus, RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  confirmRegulationUpload: vi.fn(),
  retryRegulationPreparation: vi.fn(),
}))

const RETRY_BUTTON = 'button[aria-label="Ponów przetwarzanie"]'
const OPTIONS_BUTTON = 'button[aria-label="Opcje regulacji"]'

function mountItem(
  preparationStatus: RegulationPreparationStatus,
  canManage: boolean,
  overrides: Partial<RegulationRepresentation> = {},
  score?: number,
  target: RegulationScope = 'PUBLIC',
) {
  const regulation: RegulationRepresentation = {
    id: 'uuid-1',
    createDate: '2026-09-29T10:00:00',
    presentationName: 'Ustawa testowa',
    description: null,
    regulationType: 'ACT',
    preparationStatus,
    descriptionStatus: 'NOT_REQUESTED',
    organizationId: null,
    suborganizationId: null,
    ...overrides,
  }

  return mount(RegulationItem, {
    props: { regulation, target, canManage, score },
    global: {
      stubs: {
        RouterLink: {
          template:
            '<a class="router-link-stub" :data-route="to.name" :data-regulation="to.params.regulationId"><slot /></a>',
          props: ['to'],
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

  it('renders only the organization of a regulation not assigned to a suborganization', () => {
    useOrganizationsStore().organizations = [
      {
        id: 'pwr',
        name: 'Politechnika Wrocławska',
        shortName: 'PWr',
        suborganizations: [{ id: 'w10', name: 'Wydział Mechaniczny' }],
      },
    ]

    const wrapper = mountItem('PREPARED', false, { organizationId: 'pwr' })

    expect(wrapper.find('.regulation-organization').text()).toBe('PWr')
  })

  it.each([
    ['PUBLIC', 'SearchPublicRegulation'],
    ['PRIVATE', 'SearchUserRegulation'],
  ] as const)('links a prepared %s regulation to its search page', (target, routeName) => {
    const wrapper = mountItem('PREPARED', false, {}, undefined, target)

    expect(wrapper.find('.router-link-stub').attributes()).toMatchObject({
      'data-route': routeName,
      'data-regulation': 'uuid-1',
    })
    expect(wrapper.find('.search-action').exists()).toBe(true)
  })

  it('renders similarity score when given', () => {
    const wrapper = mountItem('PREPARED', false, {}, 0.73456)

    expect(wrapper.find('.regulation-score').text()).toBe('Podobieństwo: 0.735')
  })

  it('does not render similarity score without it', () => {
    const wrapper = mountItem('PREPARED', false)

    expect(wrapper.find('.regulation-score').exists()).toBe(false)
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
    expect(wrapper.find('.search-action').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').text()).toBe('IN_PROGRESS')
    expect(wrapper.find(RETRY_BUTTON).exists()).toBe(false)
  })

  it('retries preparation when regulation failed and user can manage it', async () => {
    const wrapper = mountItem('FAILED', true)

    expect(wrapper.find('.status-badge-stub').text()).toBe('FAILED')
    const button = wrapper.find(RETRY_BUTTON)
    expect(button.exists()).toBe(true)

    vi.mocked(retryRegulationPreparation).mockResolvedValueOnce(undefined)
    await button.trigger('click')

    expect(retryRegulationPreparation).toHaveBeenCalledWith('uuid-1')
    expect(confirmRegulationUpload).not.toHaveBeenCalled()
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
    expect(shownMessages('success')).toEqual(['Ponowne przetwarzanie zostało rozpoczęte'])
  })

  it('blocks the retry button until the retry request ends', async () => {
    let finishRetry: ((value: unknown) => void) | undefined
    vi.mocked(retryRegulationPreparation).mockImplementationOnce(
      () => new Promise((resolve) => (finishRetry = resolve)),
    )
    const wrapper = mountItem('FAILED', true)
    const button = wrapper.find(RETRY_BUTTON)
    expect(button.attributes('disabled')).toBeUndefined()

    await button.trigger('click')
    expect(button.attributes('disabled')).toBeDefined()

    finishRetry?.(undefined)
    await flushPromises()
    expect(button.attributes('disabled')).toBeUndefined()
  })

  it('confirms the upload again when regulation was not started', async () => {
    const wrapper = mountItem('NOT_STARTED', true)

    vi.mocked(confirmRegulationUpload).mockResolvedValueOnce(undefined)
    await wrapper.find(RETRY_BUTTON).trigger('click')

    expect(confirmRegulationUpload).toHaveBeenCalledWith('uuid-1')
    expect(retryRegulationPreparation).not.toHaveBeenCalled()
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
  })

  it('does not emit retry when the retry request fails', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    const wrapper = mountItem('FAILED', true)

    vi.mocked(retryRegulationPreparation).mockRejectedValueOnce(new Error('boom'))
    await wrapper.find(RETRY_BUTTON).trigger('click')
    await flushPromises()

    expect(wrapper.emitted('preparation-retried')).toBeUndefined()
    expect(shownMessages('success')).toEqual([])
    expect(wrapper.find(RETRY_BUTTON).attributes('disabled')).toBeUndefined()
  })

  it('explains that a failed regulation is already being processed', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    const wrapper = mountItem('FAILED', true)

    vi.mocked(retryRegulationPreparation).mockRejectedValueOnce(createHttpError(409))
    await wrapper.find(RETRY_BUTTON).trigger('click')
    await flushPromises()

    expect(shownMessages('error')).toEqual(['Regulacja jest już przetwarzana lub przygotowana.'])
  })

  it('explains that the file of a not started regulation is missing', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    const wrapper = mountItem('NOT_STARTED', true)

    vi.mocked(confirmRegulationUpload).mockRejectedValueOnce(createHttpError(409))
    await wrapper.find(RETRY_BUTTON).trigger('click')
    await flushPromises()

    expect(shownMessages('error')).toEqual([
      'Pliku nie ma w magazynie. Usuń regulację i dodaj ją ponownie.',
    ])
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
