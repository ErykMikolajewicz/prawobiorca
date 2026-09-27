import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import PublicRegulationCard from '../PublicRegulationCard.vue'
import { retryPublicRegulationPreparation } from '@/api/generated/endpoints/regulations/regulations'
import type { regulationPreparationStatus, regulationRepresentation } from '@/types/api/regulations'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  deletePublicRegulation: vi.fn(),
  retryPublicRegulationPreparation: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

function mountCard(preparationStatus: regulationPreparationStatus, isAdmin: boolean) {
  const regulation: regulationRepresentation = {
    id: 'uuid-1',
    presentationName: 'Ustawa testowa',
    regulationType: 'ACT',
    preparationStatus,
  }

  return mount(PublicRegulationCard, {
    props: { regulation, isAdmin },
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
        ElPopconfirm: true,
      },
    },
  })
}

describe('PublicRegulationCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search action and router-link when regulation is prepared', () => {
    const wrapper = mountCard('PREPARED', false)

    expect(wrapper.find('.router-link-stub').exists()).toBe(true)
    expect(wrapper.find('.status-badge-stub').exists()).toBe(false)
    expect(wrapper.find('form.form-action').exists()).toBe(false)
  })

  it('renders status badge without retry action while preparation is in progress', () => {
    const wrapper = mountCard('IN_PROGRESS', true)

    expect(wrapper.find('.router-link-stub').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').text()).toBe('IN_PROGRESS')
    expect(wrapper.find('form.form-action').exists()).toBe(false)
  })

  it('retries preparation when regulation failed and user is admin', async () => {
    const wrapper = mountCard('FAILED', true)

    expect(wrapper.find('.status-badge-stub').text()).toBe('FAILED')
    const form = wrapper.find('form.form-action')
    expect(form.exists()).toBe(true)

    vi.mocked(retryPublicRegulationPreparation).mockResolvedValueOnce(undefined)
    await form.trigger('submit.prevent')

    expect(retryPublicRegulationPreparation).toHaveBeenCalledWith('uuid-1')
    expect(wrapper.emitted('preparation-retried')?.[0]).toEqual(['uuid-1'])
  })

  it('does not emit retry when the retry request fails', async () => {
    const wrapper = mountCard('FAILED', true)

    vi.mocked(retryPublicRegulationPreparation).mockRejectedValueOnce(new Error('boom'))
    await wrapper.find('form.form-action').trigger('submit.prevent')

    expect(wrapper.emitted('preparation-retried')).toBeUndefined()
  })

  it('does not render status, retry or search action for a non-admin when not prepared', () => {
    const wrapper = mountCard('FAILED', false)

    expect(wrapper.find('.router-link-stub').exists()).toBe(false)
    expect(wrapper.find('.status-badge-stub').exists()).toBe(false)
    expect(wrapper.find('form.form-action').exists()).toBe(false)
  })
})
