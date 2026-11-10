import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import RegulationsList from '../RegulationsList.vue'
import RegulationOrganizationFilter from '@/components/molecules/RegulationOrganizationFilter.vue'
import RegulationTypeFilter from '@/components/molecules/RegulationTypeFilter.vue'
import { createRegulation } from '@/__tests__/factories'
import type { RegulationScope } from '@/domain/regulations'
import type { RegulationRepresentation } from '@/api/generated/model'

const preparedRegulation = createRegulation({ id: '1', presentationName: 'Prepared Doc' })
const unpreparedRegulation = createRegulation({
  id: '2',
  presentationName: 'Unprepared Doc',
  preparationStatus: 'IN_PROGRESS',
})
const regulations = [preparedRegulation, unpreparedRegulation]

type ListProps = {
  regulations?: Array<RegulationRepresentation>
  target?: RegulationScope
  canManage?: boolean
  loading?: boolean
  scores?: Record<string, number>
}

function mountList(props: ListProps = {}) {
  return mount(RegulationsList, {
    props: {
      regulations,
      title: 'Publiczne regulacje',
      emptyDescription: 'Brak regulacji publicznych.',
      typeFilter: undefined,
      target: 'PUBLIC',
      canManage: true,
      ...props,
    },
    slots: { actions: '<button class="list-action">Dodaj regulacje</button>' },
    global: {
      plugins: [ElementPlus],
      stubs: {
        RegulationItem: {
          template:
            '<div class="stub-item" :data-score="score ?? \'brak\'">' +
            '{{ regulation.presentationName }}' +
            '<button class="stub-details" @click="$emit(\'open-details\', regulation.id)" />' +
            '<button class="stub-retry" @click="$emit(\'preparation-retried\', regulation.id)" />' +
            '</div>',
          props: ['regulation', 'target', 'canManage', 'score'],
        },
        RegulationDetailsDialog: {
          template:
            '<div v-if="modelValue" class="details-dialog-stub">' +
            '{{ regulation.presentationName }}' +
            '<button class="stub-update" @click="$emit(\'updated\', { ...regulation, presentationName: \'Renamed Doc\' })" />' +
            '<button class="stub-delete" @click="$emit(\'deleted\', regulation.id)" />' +
            '<button class="stub-generate" @click="$emit(\'description-generation-started\', regulation.id)" />' +
            '</div>',
          props: ['modelValue', 'regulation', 'canManage'],
        },
        RegulationTypeFilter: true,
        RegulationOrganizationFilter: true,
      },
    },
  })
}

function itemNames(wrapper: ReturnType<typeof mountList>) {
  return wrapper.findAll('.stub-item').map((item) => item.text())
}

describe('RegulationsList', () => {
  it('shows the title and the actions of the list', () => {
    const wrapper = mountList()

    expect(wrapper.find('h2').text()).toBe('Publiczne regulacje')
    expect(wrapper.find('.list-header .list-action').exists()).toBe(true)
  })

  it('displays only prepared regulations when user cannot manage them', () => {
    const wrapper = mountList({ canManage: false })

    expect(itemNames(wrapper)).toEqual(['Prepared Doc'])
  })

  it('displays all regulations (prepared and unprepared) when user can manage them', () => {
    const wrapper = mountList({ canManage: true })

    expect(itemNames(wrapper)).toEqual(['Prepared Doc', 'Unprepared Doc'])
  })

  it('passes similarity scores to regulation items', () => {
    const wrapper = mountList({ scores: { '1': 0.8 } })

    expect(wrapper.findAll('.stub-item').map((item) => item.attributes('data-score'))).toEqual([
      '0.8',
      'brak',
    ])
  })

  it('shows empty state when no regulations are visible', () => {
    const wrapper = mountList({ regulations: [unpreparedRegulation], canManage: false })

    expect(wrapper.find('.el-empty').text()).toBe('Brak regulacji publicznych.')
  })

  it('does not show empty state next to listed regulations', () => {
    const wrapper = mountList()

    expect(wrapper.find('.el-empty').exists()).toBe(false)
  })

  it('hides empty state while regulations are loading', () => {
    const wrapper = mountList({ regulations: [], loading: true })

    expect(wrapper.find('.el-empty').exists()).toBe(false)
  })

  it.each([
    ['PUBLIC', true],
    ['PRIVATE', false],
  ] as const)('shows the organization filter of a %s list: %s', (target, isShown) => {
    const wrapper = mountList({ target })

    expect(wrapper.findComponent(RegulationOrganizationFilter).exists()).toBe(isShown)
  })

  it('updates the type filter chosen by the user', async () => {
    const wrapper = mountList()

    await wrapper.findComponent(RegulationTypeFilter).setValue('ACT')

    expect(wrapper.emitted('update:typeFilter')).toEqual([['ACT']])
  })

  it('forwards a retried preparation of a regulation', async () => {
    const wrapper = mountList()

    await wrapper.findAll('.stub-retry')[1]?.trigger('click')

    expect(wrapper.emitted('regulation-preparation-retried')).toEqual([['2']])
  })

  it('does not render details dialog until a regulation is selected', () => {
    const wrapper = mountList()

    expect(wrapper.find('.details-dialog-stub').exists()).toBe(false)
  })

  it('opens details dialog for the selected regulation', async () => {
    const wrapper = mountList()

    await wrapper.findAll('.stub-details')[1]?.trigger('click')

    expect(wrapper.find('.details-dialog-stub').text()).toBe('Unprepared Doc')
  })

  it('shows refreshed data of the regulation opened in details', async () => {
    const wrapper = mountList()
    await wrapper.findAll('.stub-details')[1]?.trigger('click')

    await wrapper.setProps({
      regulations: [preparedRegulation, { ...unpreparedRegulation, presentationName: 'Ready Doc' }],
    })

    expect(wrapper.find('.details-dialog-stub').text()).toBe('Ready Doc')
  })

  it('closes details of a regulation that is no longer on the list', async () => {
    const wrapper = mountList()
    await wrapper.findAll('.stub-details')[1]?.trigger('click')

    await wrapper.setProps({ regulations: [preparedRegulation] })

    expect(wrapper.find('.details-dialog-stub').exists()).toBe(false)
  })

  it('forwards regulation changes made in details dialog', async () => {
    const wrapper = mountList()

    await wrapper.findAll('.stub-details')[0]?.trigger('click')
    await wrapper.find('.stub-update').trigger('click')
    await wrapper.find('.stub-generate').trigger('click')
    await wrapper.find('.stub-delete').trigger('click')

    expect(wrapper.emitted('regulation-updated')).toEqual([
      [{ ...preparedRegulation, presentationName: 'Renamed Doc' }],
    ])
    expect(wrapper.emitted('regulation-description-generation-started')).toEqual([['1']])
    expect(wrapper.emitted('regulation-deleted')).toEqual([['1']])
  })
})
