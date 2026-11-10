import { describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import FileSelectButton from '../FileSelectButton.vue'
import { shownMessages } from '@/__tests__/dom'

function mountButton(modelValue: File | null, label?: string) {
  return mount(FileSelectButton, {
    props: { modelValue, label },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  })
}

async function selectFile(file: File, previousFile: File | null = null) {
  const wrapper = mountButton(previousFile)
  const input = wrapper.find('input[type="file"]')
  const setValue = vi.fn()
  Object.defineProperty(input.element, 'files', { value: [file] })
  Object.defineProperty(input.element, 'value', { get: () => file.name, set: setValue })

  await input.trigger('change')
  await flushPromises()

  return { wrapper, setValue }
}

describe('FileSelectButton', () => {
  it('opens the file chooser from the button and shows the selected file name', async () => {
    const wrapper = mountButton(new File(['dummy'], 'doc.pdf'), 'Wybierz PDF')
    const openChooser = vi.spyOn(wrapper.find('input').element, 'click')

    await wrapper.find('button').trigger('click')

    expect(openChooser).toHaveBeenCalledOnce()
    expect(wrapper.find('button').text()).toBe('Wybierz PDF')
    expect(wrapper.find('.selected-file-name').text()).toBe('doc.pdf')
  })

  it('shows the default label and no file name before a file is selected', () => {
    const wrapper = mountButton(null)

    expect(wrapper.find('button').text()).toBe('Wybierz plik')
    expect(wrapper.find('.selected-file-name').exists()).toBe(false)
  })

  it('clears the selection when the file chooser is closed without a file', async () => {
    const wrapper = mountButton(new File(['previous'], 'previous.pdf'))

    await wrapper.find('input[type="file"]').trigger('change')
    await flushPromises()

    expect(wrapper.emitted('update:modelValue')).toEqual([[null]])
    expect(shownMessages('error')).toEqual([])
  })

  it('clears the input after selection so the same file can be selected again', async () => {
    const { setValue } = await selectFile(new File(['dummy'], 'doc.pdf'))

    expect(setValue).toHaveBeenCalledWith('')
  })

  it('emits an in-memory copy so later changes on disk cannot break the upload', async () => {
    const file = new File(['dummy'], 'doc.pdf', { type: 'application/pdf', lastModified: 1000 })

    const { wrapper } = await selectFile(file)

    const emitted = wrapper.emitted('update:modelValue')?.[0]?.[0] as File
    expect(emitted).not.toBe(file)
    expect(emitted.name).toBe('doc.pdf')
    expect(emitted.type).toBe('application/pdf')
    expect(emitted.lastModified).toBe(1000)
    expect(await emitted.text()).toBe('dummy')
  })

  it('clears the previous selection and shows an error when the file cannot be read', async () => {
    vi.spyOn(console, 'error').mockImplementationOnce(() => {})
    const file = new File(['dummy'], 'doc.pdf')
    vi.spyOn(file, 'arrayBuffer').mockRejectedValueOnce(new DOMException('', 'NotReadableError'))

    const { wrapper } = await selectFile(file, new File(['previous'], 'previous.pdf'))

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([null])
    expect(shownMessages('error')).toEqual(['Nie udało się odczytać pliku. Wybierz go ponownie.'])
  })
})
