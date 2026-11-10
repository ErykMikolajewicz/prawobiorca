import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import RegulationUploadDialog from '../RegulationUploadDialog.vue'
import { createTestApp } from '@/__tests__/app'
import { findButton, findOption, shownMessages } from '@/__tests__/dom'
import { createHttpError, createOrganizations } from '@/__tests__/factories'
import {
  addRegulation,
  confirmRegulationUpload,
} from '@/api/generated/endpoints/regulations/regulations'
import { useOrganizationsStore } from '@/stores/organizations'
import { uploadFileToStorage } from '@/utils/storage'

vi.mock('@/api/generated/endpoints/regulations/regulations')
vi.mock('@/utils/storage')

const uploadTarget = { id: 'regulation-9', url: 'https://storage.example.com', fields: {} }

async function mountDialog(isAdmin: boolean) {
  const { global } = await createTestApp()
  useOrganizationsStore().organizations = createOrganizations()
  const wrapper: VueWrapper = mount(RegulationUploadDialog, {
    props: {
      isAdmin,
      modelValue: false,
      'onUpdate:modelValue': (modelValue: boolean) => wrapper.setProps({ modelValue }),
    },
    global,
    attachTo: document.body,
  })
  await wrapper.setProps({ modelValue: true })
  return wrapper
}

async function selectFile(wrapper: VueWrapper, name: string) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: [new File(['pdf'], name)] })
  await input.trigger('change')
  await flushPromises()
}

async function submit() {
  await findButton('Dodaj')!.trigger('click')
  await flushPromises()
}

function nameInput(wrapper: VueWrapper) {
  return wrapper.find<HTMLInputElement>('input[placeholder="Nazwa pliku"]')
}

describe('RegulationUploadDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(addRegulation).mockResolvedValue(uploadTarget)
  })

  it('uploads a private regulation of a regular user and closes the dialog', async () => {
    const wrapper = await mountDialog(false)

    await selectFile(wrapper, 'regulamin.pdf')
    await nameInput(wrapper).setValue('Regulamin studiów')
    await findOption('Regulamin')!.trigger('click')
    await submit()

    expect(addRegulation).toHaveBeenCalledExactlyOnceWith({
      scope: 'PRIVATE',
      name: 'Regulamin studiów',
      regulationType: 'STATUTE',
      organizationId: null,
      suborganizationId: null,
      generateDescription: false,
    })
    expect(vi.mocked(uploadFileToStorage).mock.calls[0]?.[0]).toEqual(uploadTarget)
    expect(confirmRegulationUpload).toHaveBeenCalledExactlyOnceWith('regulation-9')
    expect(wrapper.emitted('created')).toEqual([
      [
        expect.objectContaining({
          id: 'regulation-9',
          presentationName: 'Regulamin studiów',
          preparationStatus: 'IN_PROGRESS',
        }),
        'PRIVATE',
      ],
    ])
    expect(findButton('Dodaj')).toBeUndefined()
  })

  it('proposes the file name as the regulation name', async () => {
    const wrapper = await mountDialog(false)

    await selectFile(wrapper, 'regulamin.pdf')

    expect(nameInput(wrapper).element.value).toBe('regulamin.pdf')
    expect(wrapper.find('.selected-file-name').text()).toBe('regulamin.pdf')
  })

  it('does not offer a regular user the options of an administrator', async () => {
    const wrapper = await mountDialog(false)

    expect(wrapper.text()).not.toContain('Wygeneruj opis przez AI')
    expect(wrapper.text()).not.toContain('Widoczność pliku')
    expect(wrapper.text()).not.toContain('Organizacja')
  })

  it('offers an organization only for a public regulation', async () => {
    const wrapper = await mountDialog(true)
    expect(wrapper.text()).not.toContain('Organizacja')

    await wrapper.find('input[type="radio"][value="PUBLIC"]').setValue(true)

    expect(wrapper.text()).toContain('Organizacja (opcjonalnie):')
  })

  it('allows choosing a suborganization only after an organization is chosen', async () => {
    const wrapper = await mountDialog(true)
    await wrapper.find('input[type="radio"][value="PUBLIC"]').setValue(true)
    const suborganizationSelect = wrapper.findAll('.el-select__wrapper')[2]!
    expect(suborganizationSelect.classes()).toContain('is-disabled')

    await findOption('Politechnika Wrocławska')!.trigger('click')

    expect(suborganizationSelect.classes()).not.toContain('is-disabled')
  })

  it('uploads a public regulation of an organization with a generated description', async () => {
    const wrapper = await mountDialog(true)

    await selectFile(wrapper, 'statut.pdf')
    await wrapper.find('input[type="radio"][value="PUBLIC"]').setValue(true)
    await wrapper.find('input[type="checkbox"]').setValue(true)
    await findOption('Politechnika Wrocławska')!.trigger('click')
    await findOption('Wydział Informatyki')!.trigger('click')
    await submit()

    expect(addRegulation).toHaveBeenCalledExactlyOnceWith({
      scope: 'PUBLIC',
      name: 'statut.pdf',
      regulationType: null,
      organizationId: 'pwr',
      suborganizationId: 'w4',
      generateDescription: true,
    })
    expect(wrapper.emitted('created')?.[0]?.[1]).toBe('PUBLIC')
  })

  it('keeps the dialog open when the upload fails', async () => {
    vi.mocked(addRegulation).mockRejectedValue(createHttpError(500))
    const wrapper = await mountDialog(false)

    await selectFile(wrapper, 'regulamin.pdf')
    await submit()

    expect(shownMessages('error')).toEqual(['Wystąpił błąd podczas dodawania pliku.'])
    expect(wrapper.emitted('created')).toBeUndefined()
    expect(findButton('Dodaj')).toBeDefined()
  })

  it('asks for a file before uploading', async () => {
    const wrapper = await mountDialog(false)

    await submit()

    expect(shownMessages('warning')).toEqual(['Wybierz plik do przesłania.'])
    expect(wrapper.emitted('created')).toBeUndefined()
    expect(findButton('Dodaj')).toBeDefined()
  })

  it('closes without uploading when cancelled', async () => {
    const wrapper = await mountDialog(false)
    await selectFile(wrapper, 'regulamin.pdf')

    await findButton('Anuluj')!.trigger('click')

    expect(findButton('Dodaj')).toBeUndefined()
    expect(addRegulation).not.toHaveBeenCalled()
  })

  it('starts with an empty form when opened again', async () => {
    const wrapper = await mountDialog(true)
    await selectFile(wrapper, 'regulamin.pdf')
    await wrapper.find('input[type="radio"][value="PUBLIC"]').setValue(true)
    await findButton('Anuluj')!.trigger('click')

    await wrapper.setProps({ modelValue: true })

    expect(nameInput(wrapper).element.value).toBe('')
    expect(wrapper.find('.selected-file-name').exists()).toBe(false)
    expect(
      wrapper.find<HTMLInputElement>('input[type="radio"][value="PRIVATE"]').element.checked,
    ).toBe(true)
  })
})
