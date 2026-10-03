import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import RegulationsList from '../RegulationsList.vue'
import type { RegulationRepresentation } from '@/api/generated/model'

vi.mock('@/api/generated/endpoints/regulations/regulations', () => ({
  deletePublicRegulation: vi.fn(),
  retryPublicRegulationPreparation: vi.fn(),
}))

const mockRegulations: RegulationRepresentation[] = [
  {
    id: '1',
    createDate: '2026-09-29T10:00:00',
    description: null,
    presentationName: 'Prepared Doc',
    preparationStatus: 'PREPARED',
    regulationType: 'ACT',
  },
  {
    id: '2',
    createDate: '2026-09-29T10:00:00',
    description: null,
    presentationName: 'Unprepared Doc',
    preparationStatus: 'IN_PROGRESS',
    regulationType: 'STATUTE',
  },
]

describe('RegulationsList', () => {
  it('displays only prepared regulations when user cannot manage them', () => {
    const wrapper = mount(RegulationsList, {
      props: {
        regulations: mockRegulations,
        title: 'Publiczne regulacje',
        emptyDescription: 'Brak regulacji publicznych.',
        typeFilter: undefined,
        target: 'public',
        canManage: false,
      },
      global: {
        directives: { loading: {} },
        stubs: {
          RouterLink: true,
          RegulationCard: {
            template: '<div class="stub-card">{{ regulation.presentationName }}</div>',
            props: ['regulation', 'target', 'canManage'],
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

  it('displays all regulations (prepared and unprepared) when user can manage them', () => {
    const wrapper = mount(RegulationsList, {
      props: {
        regulations: mockRegulations,
        title: 'Publiczne regulacje',
        emptyDescription: 'Brak regulacji publicznych.',
        typeFilter: undefined,
        target: 'public',
        canManage: true,
      },
      global: {
        directives: { loading: {} },
        stubs: {
          RouterLink: true,
          RegulationCard: {
            template: '<div class="stub-card">{{ regulation.presentationName }}</div>',
            props: ['regulation', 'target', 'canManage'],
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
    const wrapper = mount(RegulationsList, {
      props: {
        regulations: [
          {
            id: '2',
            createDate: '2026-09-29T10:00:00',
            description: null,
            presentationName: 'Unprepared Doc',
            preparationStatus: 'IN_PROGRESS',
            regulationType: 'STATUTE',
          },
        ],
        title: 'Publiczne regulacje',
        emptyDescription: 'Brak regulacji publicznych.',
        typeFilter: undefined,
        target: 'public',
        canManage: false,
      },
      global: {
        directives: { loading: {} },
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

  it('hides empty state while regulations are loading', () => {
    const wrapper = mount(RegulationsList, {
      props: {
        regulations: [],
        title: 'Publiczne regulacje',
        emptyDescription: 'Brak regulacji publicznych.',
        typeFilter: undefined,
        target: 'public',
        canManage: false,
        loading: true,
      },
      global: {
        directives: { loading: {} },
        stubs: {
          RegulationTypeFilter: true,
          ElEmpty: {
            template: '<div class="el-empty-stub">Brak regulacji</div>',
          },
        },
      },
    })

    expect(wrapper.find('.el-empty-stub').exists()).toBe(false)
  })

  it('forwards regulation update from card', async () => {
    const updatedRegulation = { ...mockRegulations[0]!, presentationName: 'Renamed Doc' }
    const wrapper = mount(RegulationsList, {
      props: {
        regulations: mockRegulations,
        title: 'Publiczne regulacje',
        emptyDescription: 'Brak regulacji publicznych.',
        typeFilter: undefined,
        target: 'public',
        canManage: true,
      },
      global: {
        directives: { loading: {} },
        stubs: {
          RegulationCard: {
            template:
              '<button class="stub-card" @click="$emit(\'updated\', { ...regulation, presentationName: \'Renamed Doc\' })" />',
            props: ['regulation', 'target', 'canManage'],
          },
          RegulationTypeFilter: true,
          ElEmpty: true,
        },
      },
    })

    await wrapper.findAll('.stub-card')[0]?.trigger('click')

    expect(wrapper.emitted('regulation-updated')?.[0]).toEqual([updatedRegulation])
  })
})
