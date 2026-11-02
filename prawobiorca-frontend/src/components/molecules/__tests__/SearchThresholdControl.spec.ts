import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchThresholdControl from '../SearchThresholdControl.vue'

function mountControl(modelValue: number, canUseAdvanced: boolean) {
  return mount(SearchThresholdControl, {
    props: { modelValue, canUseAdvanced },
    global: {
      stubs: {
        ElSlider: { template: '<div class="slider-stub" />' },
        ElSelect: { template: '<div class="select-stub"><slot /></div>' },
        ElOption: true,
        ElCheckbox: {
          template:
            '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
          props: ['modelValue'],
        },
      },
    },
  })
}

describe('SearchThresholdControl', () => {
  it('shows the slider for a custom threshold when advanced mode is available', () => {
    const wrapper = mountControl(0.65, true)

    expect(wrapper.find('.slider-stub').exists()).toBe(true)
    expect(wrapper.find('.select-stub').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('resets a custom threshold to default when advanced mode is unavailable', () => {
    const wrapper = mountControl(0.65, false)

    expect(wrapper.find('.select-stub').exists()).toBe(true)
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([0.5])
  })

  it('resets a custom threshold to default after leaving advanced mode', async () => {
    const wrapper = mountControl(0.65, true)

    await wrapper.find('input[type="checkbox"]').setValue(false)

    expect(wrapper.find('.select-stub').exists()).toBe(true)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([0.5])
  })
})
