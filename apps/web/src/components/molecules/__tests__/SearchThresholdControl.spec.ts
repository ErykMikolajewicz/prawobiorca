import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import SearchThresholdControl from '../SearchThresholdControl.vue'
import { findOption } from '@/__tests__/dom'

function mountControl(modelValue: number, canUseAdvanced: boolean) {
  return mount(SearchThresholdControl, {
    props: { modelValue, canUseAdvanced },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

describe('SearchThresholdControl', () => {
  it('shows the slider for a custom threshold when advanced mode is available', () => {
    const wrapper = mountControl(0.65, true)

    expect(wrapper.find('.el-slider').exists()).toBe(true)
    expect(wrapper.find('.el-select').exists()).toBe(false)
    expect(wrapper.find('.threshold-value').text()).toBe('0.65')
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('shows presets for a preset threshold even when advanced mode is available', () => {
    const wrapper = mountControl(0.7, true)

    expect(wrapper.find('.el-select').exists()).toBe(true)
    expect(wrapper.find('.el-slider').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('resets a custom threshold to default when advanced mode is unavailable', () => {
    const wrapper = mountControl(0.65, false)

    expect(wrapper.find('.el-select').exists()).toBe(true)
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([0.5])
  })

  it('resets a custom threshold to default after leaving advanced mode', async () => {
    const wrapper = mountControl(0.65, true)

    await wrapper.find('input[type="checkbox"]').setValue(false)

    expect(wrapper.find('.el-select').exists()).toBe(true)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([0.5])
  })

  it('keeps a preset threshold after entering advanced mode', async () => {
    const wrapper = mountControl(0.7, true)

    await wrapper.find('input[type="checkbox"]').setValue(true)

    expect(wrapper.find('.el-slider').exists()).toBe(true)
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('sets the threshold of the chosen preset', async () => {
    const wrapper = mountControl(0.5, false)

    await findOption('Bardzo ścisły')!.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([[0.8]])
  })
})
