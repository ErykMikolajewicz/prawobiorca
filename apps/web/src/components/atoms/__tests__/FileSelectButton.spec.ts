import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import FileSelectButton from '../FileSelectButton.vue'

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

async function selectFile(file: File, previousFile: File | null = null) {
  const wrapper = mount(FileSelectButton, {
    props: { modelValue: previousFile },
    global: { stubs: { ElButton: true } },
  })
  const input = wrapper.find('input[type="file"]')
  const setValue = vi.fn()
  Object.defineProperty(input.element, 'files', { value: [file] })
  Object.defineProperty(input.element, 'value', { get: () => file.name, set: setValue })

  await input.trigger('change')
  await flushPromises()

  return { wrapper, setValue }
}

describe('FileSelectButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
    expect(ElMessage.error).toHaveBeenCalledWith(
      'Nie udało się odczytać pliku. Wybierz go ponownie.',
    )
  })
})
