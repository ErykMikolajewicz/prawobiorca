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
    organizationId: null,
    suborganizationId: null,
  },
  {
    id: '2',
    createDate: '2026-09-29T10:00:00',
    description: null,
    presentationName: 'Unprepared Doc',
    preparationStatus: 'IN_PROGRESS',
    regulationType: 'STATUTE',
    organizationId: null,
    suborganizationId: null,
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
          RegulationItem: {
            template: '<div class="stub-card">{{ regulation.presentationName }}</div>',
            props: ['regulation', 'target', 'canManage'],
          },
          RegulationTypeFilter: true,
          RegulationOrganizationFilter: true,
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
          RegulationItem: {
            template: '<div class="stub-card">{{ regulation.presentationName }}</div>',
            props: ['regulation', 'target', 'canManage'],
          },
          RegulationTypeFilter: true,
          RegulationOrganizationFilter: true,
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
            organizationId: null,
            suborganizationId: null,
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
          RegulationOrganizationFilter: true,
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
          RegulationOrganizationFilter: true,
          ElEmpty: {
            template: '<div class="el-empty-stub">Brak regulacji</div>',
          },
        },
      },
    })

    expect(wrapper.find('.el-empty-stub').exists()).toBe(false)
  })

  it('does not render details dialog until a regulation is selected', () => {
    const wrapper = mountWithDetailsDialog()

    expect(wrapper.find('.details-dialog-stub').exists()).toBe(false)
  })

  it('opens details dialog for the selected regulation', async () => {
    const wrapper = mountWithDetailsDialog()

    await wrapper.findAll('.stub-item')[1]?.trigger('click')

    expect(wrapper.find('.details-dialog-stub').text()).toBe('Unprepared Doc')
  })

  it('forwards regulation update and delete from details dialog', async () => {
    const wrapper = mountWithDetailsDialog()

    await wrapper.findAll('.stub-item')[0]?.trigger('click')
    await wrapper.find('.stub-update').trigger('click')
    await wrapper.find('.stub-delete').trigger('click')

    expect(wrapper.emitted('regulation-updated')?.[0]).toEqual([
      { ...mockRegulations[0]!, presentationName: 'Renamed Doc' },
    ])
    expect(wrapper.emitted('regulation-deleted')?.[0]).toEqual(['1'])
  })
})

function mountWithDetailsDialog() {
  return mount(RegulationsList, {
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
        RegulationItem: {
          template: '<button class="stub-item" @click="$emit(\'open-details\', regulation.id)" />',
          props: ['regulation', 'target', 'canManage'],
        },
        RegulationDetailsDialog: {
          template:
            '<div v-if="modelValue" class="details-dialog-stub">' +
            '{{ regulation.presentationName }}' +
            '<button class="stub-update" @click="$emit(\'updated\', { ...regulation, presentationName: \'Renamed Doc\' })" />' +
            '<button class="stub-delete" @click="$emit(\'deleted\', regulation.id)" />' +
            '</div>',
          props: ['modelValue', 'regulation', 'target', 'canManage'],
        },
        RegulationTypeFilter: true,
        RegulationOrganizationFilter: true,
        ElEmpty: true,
      },
    },
  })
}
