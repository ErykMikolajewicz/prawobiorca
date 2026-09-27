import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PublicRegulationsList from '../PublicRegulationsList.vue'
import type { RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  deletePublicRegulation: vi.fn(),
  retryPublicRegulationPreparation: vi.fn(),
}))

const mockRegulations: RegulationRepresentation[] = [
  {
    id: '1',
    presentationName: 'Prepared Doc',
    preparationStatus: 'PREPARED',
    regulationType: 'ACT',
  },
  {
    id: '2',
    presentationName: 'Unprepared Doc',
    preparationStatus: 'IN_PROGRESS',
    regulationType: 'STATUTE',
  },
]

describe('PublicRegulationsList', () => {
  it('displays only prepared regulations when user is not admin', () => {
    const wrapper = mount(PublicRegulationsList, {
      props: {
        regulations: mockRegulations,
        typeFilter: undefined,
        isAdmin: false,
      },
      global: {
        stubs: {
          RouterLink: true,
          PublicRegulationCard: {
            template: '<div class="stub-card">{{ regulation.presentationName }}</div>',
            props: ['regulation', 'isAdmin'],
          },
          RegulationTypeFilter: true,
          ElEmpty: true,
        },
      },
    })

    const cards = wrapper.findAll('.stub-card')
    expect(cards).toHaveLength(1)
    expect(cards[0]?.text()).toBe('Prepared Doc')
  })

  it('displays all regulations (prepared and unprepared) when user is admin', () => {
    const wrapper = mount(PublicRegulationsList, {
      props: {
        regulations: mockRegulations,
        typeFilter: undefined,
        isAdmin: true,
      },
      global: {
        stubs: {
          RouterLink: true,
          PublicRegulationCard: {
            template: '<div class="stub-card">{{ regulation.presentationName }}</div>',
            props: ['regulation', 'isAdmin'],
          },
          RegulationTypeFilter: true,
          ElEmpty: true,
        },
      },
    })

    const cards = wrapper.findAll('.stub-card')
    expect(cards).toHaveLength(2)
  })

  it('shows empty state when no regulations are visible', () => {
    const wrapper = mount(PublicRegulationsList, {
      props: {
        regulations: [
          {
            id: '2',
            presentationName: 'Unprepared Doc',
            preparationStatus: 'IN_PROGRESS',
            regulationType: 'STATUTE',
          },
        ],
        typeFilter: undefined,
        isAdmin: false,
      },
      global: {
        stubs: {
          RegulationTypeFilter: true,
          ElEmpty: {
            template: '<div class="el-empty-stub">Brak regulacji</div>',
          },
        },
      },
    })

    expect(wrapper.find('.el-empty-stub').exists()).toBe(true)
  })
})
