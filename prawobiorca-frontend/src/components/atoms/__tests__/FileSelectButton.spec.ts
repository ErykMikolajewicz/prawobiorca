import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FileSelectButton from '../FileSelectButton.vue'

describe('FileSelectButton', () => {
  it('clears the input after selection so the same file can be selected again', async () => {
    const wrapper = mount(FileSelectButton, {
      props: { modelValue: null },
      global: { stubs: { ElButton: true } },
    })
    const file = new File(['dummy'], 'doc.pdf', { type: 'application/pdf' })
    const input = wrapper.find('input[type="file"]')
    const setValue = vi.fn()
    Object.defineProperty(input.element, 'files', { value: [file] })
    Object.defineProperty(input.element, 'value', { get: () => 'doc.pdf', set: setValue })

    await input.trigger('change')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([file])
    expect(setValue).toHaveBeenCalledWith('')
  })
})
