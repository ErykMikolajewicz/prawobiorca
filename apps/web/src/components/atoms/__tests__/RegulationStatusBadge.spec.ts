import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus, { ElTooltip } from 'element-plus'
import RegulationStatusBadge from '../RegulationStatusBadge.vue'
import type {
  RegulationPreparationFailureReason,
  RegulationPreparationStatus,
} from '@/api/generated/model'

function mountBadge(
  preparationStatus: RegulationPreparationStatus,
  failureReason: RegulationPreparationFailureReason | null = null,
) {
  return mount(RegulationStatusBadge, {
    props: { preparationStatus, failureReason },
    global: { plugins: [ElementPlus] },
  })
}

describe('RegulationStatusBadge', () => {
  it('explains the failure reason of a failed preparation', () => {
    const wrapper = mountBadge('FAILED', 'INCOMPLETE_DOCUMENT')

    expect(wrapper.find('.el-tag').text()).toBe('Błąd przetwarzania')
    expect(wrapper.findComponent(ElTooltip).props()).toMatchObject({
      disabled: false,
      content: expect.stringContaining('Nie udało się odczytać całego dokumentu'),
    })
  })

  it.each<[RegulationPreparationStatus, RegulationPreparationFailureReason | null]>([
    ['FAILED', null],
    ['IN_PROGRESS', 'INCOMPLETE_DOCUMENT'],
  ])('does not explain %s preparation with reason %s', (preparationStatus, failureReason) => {
    const wrapper = mountBadge(preparationStatus, failureReason)

    expect(wrapper.find('.el-tag').exists()).toBe(true)
    expect(wrapper.findComponent(ElTooltip).props('disabled')).toBe(true)
  })

  it('does not render a badge for a prepared regulation', () => {
    const wrapper = mountBadge('PREPARED')

    expect(wrapper.find('.el-tag').exists()).toBe(false)
  })
})
